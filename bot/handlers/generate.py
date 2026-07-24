import asyncio
import logging
import time
from datetime import date

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.database.repositories.credits import CreditsRepository
from bot.database.repositories.generation import GenerationRepository
from bot.database.repositories.user import UserRepository
from bot.handlers.states import GenerateState
from bot.keyboards.generation import get_cancel_keyboard, get_generation_keyboard
from bot.keyboards.main import get_main_keyboard
from bot.services.ai_providers.info import PROVIDER_INFO
from bot.services.google_sheets import GoogleSheetsService
from bot.services.image import generate_image

logger = logging.getLogger(__name__)

router = Router(name="generate")

IGNORED_BUTTONS = ("🎨", "💬", "🤖", "👤", "⭐", "ℹ️", "🎬", "🎰", "💰")

IMAGE_CREDIT_COSTS = {
    "pollinations": 0,
    "dalle": 6,
    "stability": 6,
    "flux": 6,
}


def _progress_bar(pct: int) -> str:
    filled = pct // 5
    empty = 20 - filled
    return f"[{'█' * filled}{'░' * empty}] {pct}%"


async def _update_timer(message: Message, start: float, provider_display: str, provider):
    while True:
        await asyncio.sleep(3)
        elapsed = time.time() - start
        pct = provider.estimate_progress(elapsed)
        try:
            await message.edit_text(
                f"⏳ Генерирую изображение...\n"
                f"🤖 Модель: {provider_display}\n\n"
                f"  {_progress_bar(pct)}\n\n"
                f"⏱ Прошло: {int(elapsed)} сек"
            )
        except Exception:
            pass


@router.message(lambda m: m.text == "🎨 Создать фото")
async def btn_generate(message: Message, state: FSMContext, session) -> None:
    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("Отправьте /start", reply_markup=get_main_keyboard(message.from_user.id))
        return

    from bot.database.repositories.admin_settings import AdminRepository
    admin_repo = AdminRepository(session)
    admin_settings = await admin_repo.get()

    today = date.today()
    if user.last_generation_date != today:
        user.generations_today = 0
        user.last_generation_date = today
        await session.commit()

    if not admin_settings.free_mode and user.generations_today >= user.daily_limit:
        await message.answer(
            "⚠️ Лимит генераций на сегодня исчерпан "
            f"({user.daily_limit}/день).\n\n"
            "💰 Купите кредиты для продолжения!",
            reply_markup=get_main_keyboard(message.from_user.id),
        )
        return

    credits_repo = CreditsRepository(session)
    cost = IMAGE_CREDIT_COSTS.get(user.selected_provider, 6)
    if admin_settings.free_mode:
        cost = 0
    if cost > 0 and not await credits_repo.has_enough(message.from_user.id, cost):
        await message.answer(
            f"❌ Недостаточно кредитов!\n"
            f"Нужно: {cost} кредитов\n"
            f"У вас: {user.credits} кредитов\n\n"
            "💰 Купите кредиты для продолжения.",
            reply_markup=get_main_keyboard(message.from_user.id),
        )
        return

    await state.set_state(GenerateState.waiting_prompt)
    await message.answer(
        "Опишите изображение, которое хотите получить.\n\n"
        'Например: <i>"Кот-космонавт на фоне Луны, цифровая живопись"</i>\n\n'
        f"💰 Стоимость: {cost} кредитов\n\n"
        "❌ Для отмены нажмите кнопку ниже.",
        reply_markup=get_cancel_keyboard(),
    )


@router.callback_query(lambda c: c.data == "cancel_generation")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Генерация отменена.")
    await callback.message.answer(
        "Выберите действие:", reply_markup=get_main_keyboard(callback.from_user.id)
    )
    await callback.answer()


@router.message(GenerateState.waiting_prompt)
async def handle_prompt(message: Message, state: FSMContext, session) -> None:
    if not message.text:
        await message.answer("Отправьте текстовое описание.")
        return

    if message.text.startswith(IGNORED_BUTTONS):
        return

    prompt = message.text.strip()
    if not prompt:
        await message.answer("Промпт не может быть пустым. Попробуйте ещё раз.")
        return

    await state.clear()

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("Отправьте /start", reply_markup=get_main_keyboard(message.from_user.id))
        return

    provider_key = user.selected_provider
    provider_info = PROVIDER_INFO.get(provider_key, {})
    provider_display = f"{provider_info.get('emoji', '')} {provider_info.get('name', provider_key)}"

    credits_repo = CreditsRepository(session)
    cost = IMAGE_CREDIT_COSTS.get(provider_key, 6)

    start = time.time()
    loading_msg = await message.answer(
        f"⏳ Генерирую изображение...\n"
        f"🤖 Модель: {provider_display}\n\n"
        f"  {_progress_bar(10)}\n\n"
        f"⏱ Прошло: 0 сек"
    )

    from bot.services.ai_providers.registry import ProviderRegistry
    try:
        provider_obj = ProviderRegistry.get(provider_key)
    except KeyError:
        provider_obj = None

    timer_task = None
    if provider_obj and hasattr(provider_obj, 'estimate_progress'):
        timer_task = asyncio.create_task(
            _update_timer(loading_msg, start, provider_display, provider_obj)
        )

    try:
        image_bytes, file_path, provider_name = await generate_image(
            prompt, provider_name=provider_key
        )

        if cost > 0:
            await credits_repo.spend_credits(message.from_user.id, cost)

        gen_repo = GenerationRepository(session)
        generation = await gen_repo.create(
            user_id=user.id,
            prompt=prompt,
            provider=provider_name,
            image_path=file_path,
        )

        user.generations_today += 1
        user.last_generation_date = date.today()
        await session.commit()

        from bot.config import settings
        sheets = GoogleSheetsService(webhook_url=settings.google_sheets_url)
        await sheets.log_transaction(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            type_label="Фото",
            model=provider_name,
            kie_credits=0,
            tg_credits=cost,
        )

        elapsed = int(time.time() - start)
        await loading_msg.delete()

        new_balance = await credits_repo.get_balance(message.from_user.id)
        photo = BufferedInputFile(image_bytes, filename="photo.jpg")
        caption = (
            f"🖼 <b>Генерация #{generation.id}</b>\n\n"
            f"📝 Промпт: <i>{prompt}</i>\n"
            f"🤖 Модель: {provider_display}\n"
            f"⏱ Время: {elapsed} сек\n"
            f"💰 Баланс: {new_balance} кредитов"
        )

        await message.answer_photo(
            photo=photo,
            caption=caption,
            reply_markup=get_generation_keyboard(generation.id),
        )

    except Exception as e:
        logger.exception("Generation failed: %s", e)
        from bot.config import settings
        sheets = GoogleSheetsService(webhook_url=settings.google_sheets_url)
        await sheets.log_transaction(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            type_label="Фото",
            model=provider_key,
            kie_credits=0,
            tg_credits=0,
            status="Ошибка",
        )
        elapsed = int(time.time() - start)
        try:
            await loading_msg.edit_text(
                f"❌ Ошибка генерации (заняло {elapsed} сек).\n"
                f"Попробуйте ещё раз позже.\n\n"
                f"<code>{type(e).__name__}: {str(e)[:100]}</code>"
            )
        except Exception:
            pass
        await message.answer(
            "Выберите действие:", reply_markup=get_main_keyboard(message.from_user.id)
        )
    finally:
        if timer_task:
            timer_task.cancel()
            try:
                await timer_task
            except asyncio.CancelledError:
                pass


@router.callback_query(lambda c: c.data.startswith("repeat:"))
async def callback_repeat(callback: CallbackQuery, session):
    generation_id = int(callback.data.split(":")[1])
    gen_repo = GenerationRepository(session)
    generation = await gen_repo.get_by_id(generation_id)

    if not generation:
        await callback.answer("Генерация не найдена", show_alert=True)
        return

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    today = date.today()
    if user.last_generation_date != today:
        user.generations_today = 0
        user.last_generation_date = today
        await session.commit()

    from bot.database.repositories.admin_settings import AdminRepository
    admin_repo = AdminRepository(session)
    admin_settings = await admin_repo.get()

    if not admin_settings.free_mode and user.generations_today >= user.daily_limit:
        await callback.answer("Лимит генераций на сегодня исчерпан", show_alert=True)
        return

    credits_repo = CreditsRepository(session)
    cost = IMAGE_CREDIT_COSTS.get(generation.provider, 6)
    if admin_settings.free_mode:
        cost = 0
    if cost > 0 and not await credits_repo.has_enough(callback.from_user.id, cost):
        await callback.answer("Недостаточно кредитов", show_alert=True)
        return

    await callback.answer()

    provider_info = PROVIDER_INFO.get(generation.provider, {})
    provider_display = f"{provider_info.get('emoji', '')} {provider_info.get('name', generation.provider)}"

    start = time.time()
    loading_msg = await callback.message.answer(
        f"⏳ Повторная генерация...\n"
        f"🤖 Модель: {provider_display}\n\n"
        f"  {_progress_bar(10)}\n\n"
        f"⏱ Прошло: 0 сек"
    )

    from bot.services.ai_providers.registry import ProviderRegistry
    try:
        provider_obj = ProviderRegistry.get(generation.provider)
    except KeyError:
        provider_obj = None

    timer_task = None
    if provider_obj and hasattr(provider_obj, 'estimate_progress'):
        timer_task = asyncio.create_task(
            _update_timer(loading_msg, start, provider_display, provider_obj)
        )

    try:
        provider_key = generation.provider
        image_bytes, file_path, provider_name = await generate_image(
            generation.prompt, provider_name=provider_key
        )

        if cost > 0:
            await credits_repo.spend_credits(callback.from_user.id, cost)

        new_gen = await gen_repo.create(
            user_id=generation.user_id,
            prompt=generation.prompt,
            provider=provider_name,
            image_path=file_path,
        )

        if user:
            user.generations_today += 1
            user.last_generation_date = date.today()
            await session.commit()

        from bot.config import settings
        sheets = GoogleSheetsService(webhook_url=settings.google_sheets_url)
        await sheets.log_transaction(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            type_label="Фото",
            model=provider_name,
            kie_credits=0,
            tg_credits=cost,
        )

        elapsed = int(time.time() - start)
        await loading_msg.delete()

        new_balance = await credits_repo.get_balance(callback.from_user.id)
        provider_info = PROVIDER_INFO.get(provider_name, {})
        provider_display = f"{provider_info.get('emoji', '')} {provider_info.get('name', provider_name)}"

        photo = BufferedInputFile(image_bytes, filename="photo.jpg")
        await callback.message.answer_photo(
            photo=photo,
            caption=(
                f"🖼 <b>Генерация #{new_gen.id}</b>\n\n"
                f"📝 Промпт: <i>{generation.prompt}</i>\n"
                f"🤖 Модель: {provider_display}\n"
                f"⏱ Время: {elapsed} сек\n"
                f"💰 Баланс: {new_balance} кредитов"
            ),
            reply_markup=get_generation_keyboard(new_gen.id),
        )

    except Exception as e:
        logger.exception("Repeat generation failed: %s", e)
        from bot.config import settings
        sheets = GoogleSheetsService(webhook_url=settings.google_sheets_url)
        await sheets.log_transaction(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            type_label="Фото",
            model=generation.provider,
            kie_credits=0,
            tg_credits=0,
            status="Ошибка",
        )
        elapsed = int(time.time() - start)
        try:
            await loading_msg.edit_text(
                f"❌ Ошибка генерации (заняло {elapsed} сек).\n\n"
                f"<code>{type(e).__name__}: {str(e)[:100]}</code>"
            )
        except Exception:
            pass
        await callback.message.answer(
            "Выберите действие:", reply_markup=get_main_keyboard(callback.from_user.id)
        )
    finally:
        if timer_task:
            timer_task.cancel()
            try:
                await timer_task
            except asyncio.CancelledError:
                pass


@router.callback_query(lambda c: c.data.startswith("edit:"))
async def callback_edit(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GenerateState.waiting_prompt)
    await callback.message.answer(
        "✏️ Введите новый промпт для изображения:",
        reply_markup=get_cancel_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("download:"))
async def callback_download(callback: CallbackQuery, session):
    generation_id = int(callback.data.split(":")[1])
    gen_repo = GenerationRepository(session)
    generation = await gen_repo.get_by_id(generation_id)

    if not generation or not generation.image_path:
        await callback.answer("Изображение не найдено", show_alert=True)
        return

    from pathlib import Path

    image_path = Path(generation.image_path)
    if not image_path.exists():
        await callback.answer("Файл не найден на сервере", show_alert=True)
        return

    await callback.answer()
    from aiogram.types import FSInputFile

    await callback.message.answer_document(
        document=FSInputFile(image_path),
        caption=f"⬇️ Генерация #{generation.id} — {generation.prompt}",
    )
