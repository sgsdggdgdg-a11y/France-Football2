import telegram
import json
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- تنظیمات شما (Configuration) ---
TOKEN = "7817180013:AAEeBOGXDOHCQ4P7YKXykLgaN9-QblNtmgU" 
ADMIN_ID = 6888966350  
GROUP_ID = -1003118241152  
CONTENT_FILE = "gold_ball_rank.json"
BLACKLIST_FILE = "blacklist.json" # فایل جدید برای ذخیره لیست سیاه

# --- توابع مدیریت ذخیره سازی (JSON) ---

def load_content():
    """محتوای رتبه بندی را از فایل JSON بارگذاری می کند."""
    if os.path.exists(CONTENT_FILE):
        try:
            with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
    return None

def save_content(content):
    """محتوای رتبه بندی را در فایل JSON ذخیره می کند."""
    with open(CONTENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=4)

def clear_content():
    """محتوای رتبه بندی را پاک کرده و فایل را حذف می کند."""
    if os.path.exists(CONTENT_FILE):
        os.remove(CONTENT_FILE)

# --- توابع مدیریت لیست سیاه (Blacklist) ---

def load_blacklist():
    """لیست سیاه کاربران را از فایل JSON بارگذاری می کند."""
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
                # آیدی ها به صورت ست (Set) و رشته (String) ذخیره می شوند
                return set(json.load(f))
        except json.JSONDecodeError:
            return set()
    return set()

def save_blacklist(blacklist_set):
    """لیست سیاه کاربران را در فایل JSON ذخیره می کند."""
    with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
        # تبدیل ست به لیست برای ذخیره سازی در JSON
        json.dump(list(blacklist_set), f, ensure_ascii=False, indent=4)

def is_user_blacklisted(user_id):
    """بررسی می کند که آیا کاربر در لیست سیاه است یا خیر."""
    blacklist = load_blacklist()
    return str(user_id) in blacklist 

# --- توابع کیبورد ---

def get_main_keyboard(is_admin):
    """ایجاد کیبورد اصلی (برای کاربران و ادمین)."""
    keyboard = [
        [KeyboardButton("✉️ ارسال پیام به گروه فرانس فوتبال")], 
        [KeyboardButton("🏆 رتبه بندی توپ طلا")]
    ]
    if is_admin:
        # اضافه کردن دستورات مدیریت
        keyboard.append([KeyboardButton("/rank ⚙️"), KeyboardButton("/blacklist 🚫")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_blacklist_keyboard():
    """ایجاد کیبورد مدیریت لیست سیاه (فقط برای ادمین)."""
    keyboard = [
        [KeyboardButton("➕ افزودن آیدی به لیست سیاه"), KeyboardButton("➖ حذف آیدی از لیست سیاه")],
        [KeyboardButton("👁️ مشاهده لیست سیاه فعلی")],
        [KeyboardButton("بازگشت به منوی اصلی /start")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- توابع مربوط به بخش فوروارد (هسته) ---

async def perform_forwarding(update: Update, context: ContextTypes.DEFAULT_TYPE, message_to_forward) -> None:
    """منطق واقعی ارسال پیام به ادمین (با نام) و گروه (ناشناس)."""
    user = update.effective_user
    
    # ۱. ارسال به ادمین (مدیر) - همراه با نام فرستنده
    try:
        caption_text = f"✉️ پیام جدید از: {user.full_name} (ID: {user.id})"
        await context.bot.send_message(chat_id=ADMIN_ID, text=caption_text)
        await message_to_forward.forward(chat_id=ADMIN_ID)
    except telegram.error.TelegramError as e:
        print(f"Error forwarding to Admin: {e}")

    # ۲. ارسال به گروه - کاملاً ناشناس
    try:
        if message_to_forward.text:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=message_to_forward.text,
                disable_web_page_preview=True
            )
        elif message_to_forward.photo:
            file_id = message_to_forward.photo[-1].file_id
            caption = message_to_forward.caption if message_to_forward.caption else ""
            await context.bot.send_photo(chat_id=GROUP_ID, photo=file_id, caption=caption)
        else:
            await context.bot.copy_message(
                chat_id=GROUP_ID,
                from_chat_id=message_to_forward.chat_id,
                message_id=message_to_forward.message_id
            )
    except telegram.error.TelegramError as e:
        print(f"Error sending anonymous message to Group: {e}")
        
    # ۳. پیام تأیید به کاربر عادی
    await update.message.reply_text("✅ پیام شما با موفقیت و به صورت ناشناس به گروه فرانس فوتبال ارسال شد.")

# --- توابع اصلی دستورات و منطق منوها ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دستور /start را مدیریت کرده و منوی اصلی را نمایش می دهد."""
    
    # **بررسی لیست سیاه (Global Check)**
    if is_user_blacklisted(update.effective_user.id):
        await update.message.reply_text("🚫 شما از استفاده از این ربات مسدود شده‌اید.")
        return

    context.user_data.clear()

    is_admin = update.effective_user.id == ADMIN_ID
    reply_markup = get_main_keyboard(is_admin)

    await update.message.reply_text(
        "👋 خوش آمدید! لطفا یک گزینه را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def rank_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دستور /rank را مدیریت می کند و منوی اقدامات را نمایش می دهد (فقط ادمین)."""
    # بررسی لیست سیاه ضروری نیست چون فقط ادمین می تواند استفاده کند
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ شما اجازه استفاده از این دستور را ندارید.")
        return
        
    context.user_data.clear()
    context.user_data['waiting_for_rank_action'] = True

    keyboard = [
        [KeyboardButton("➕ ذخیره‌ی محتوای جدید")],
        [KeyboardButton("🗑️ پاک کردن محتوای فعلی")],
        [KeyboardButton("بازگشت به منوی اصلی /start")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "⚙️ پنل مدیریت رتبه بندی توپ طلا. لطفاً یک اقدام را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def blacklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دستور /blacklist را مدیریت می کند و منوی مدیریت لیست سیاه را نمایش می دهد (فقط ادمین)."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ شما اجازه استفاده از این دستور را ندارید.")
        return
        
    context.user_data.clear()
    context.user_data['blacklist_state'] = 'main' # حالت اصلی مدیریت لیست سیاه

    await update.message.reply_text(
        "🚫 پنل مدیریت لیست سیاه. لطفاً یک اقدام را انتخاب کنید:",
        reply_markup=get_blacklist_keyboard()
    )

async def send_gold_ball_rank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """محتوای رتبه بندی ذخیره شده را برای کاربر ارسال می کند."""
    
    content = load_content()
    
    if content is None:
        await update.message.reply_text("در حال حاضر محتوای رتبه بندی توپ طلا توسط مدیر تنظیم نشده است. 😔")
        return

    try:
        if content['type'] == 'text':
            await update.message.reply_text(content['data'])
        elif content['type'] == 'photo':
            await update.message.reply_photo(photo=content['data'])
        else:
            await update.message.reply_text("خطا: محتوای ذخیره شده از نوع نامشخصی است. 🧐")

    except telegram.error.TelegramError as e:
         await update.message.reply_text(f"خطا در ارسال محتوا: {e}")

# --- هندلرهای مرکزی پیام‌ها ---

async def handle_private_non_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت پیام‌های غیرمتنی (مانند عکس)."""
    message = update.effective_message
    user = update.effective_user
    
    # **۱. بررسی لیست سیاه (Global Check)**
    if is_user_blacklisted(user.id):
        await update.message.reply_text("🚫 شما از استفاده از این ربات مسدود شده‌اید.")
        return
    
    # **۲. فوروارد در حالت انتظار (اولویت اول برای کاربران)**
    if context.user_data.get('waiting_for_forward') == True and user.id != ADMIN_ID:
        await perform_forwarding(update, context, message)
        return

    # **۳. Admin Content Saving (for Photo)**
    if user.id == ADMIN_ID and context.user_data.get('waiting_for_rank_content'):
        if message.photo:
            await update.message.reply_text("انتخاب شما دریافت شد. ذخیره‌سازی در حال انجام...") 
            file_id = message.photo[-1].file_id
            new_content = {'type': 'photo', 'data': file_id}
            save_content(new_content)
            context.user_data['waiting_for_rank_content'] = False
            await update.message.reply_text("⭐ محتوای رتبه بندی توپ طلا با موفقیت **ذخیره شد** و دائمی است!",
                                            reply_markup=get_main_keyboard(True))
            return
        else:
             await update.message.reply_text("نوع محتوای ارسالی پشتیبانی نشد. لطفاً فقط متن یا عکس ارسال کنید.",
                                              reply_markup=get_main_keyboard(True))
             return
    
    # **۴. Fallback (Not in forwarding state)**
    if user.id != ADMIN_ID:
         await update.message.reply_text("لطفاً ابتدا یکی از گزینه‌های منو را انتخاب کنید. برای ارسال پیام، دکمه '✉️ ارسال پیام به گروه فرانس فوتبال' را بزنید.")
         return

async def handle_private_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت پیام‌های متنی (دکمه‌ها و پیام‌های عادی)."""
    
    text = update.message.text
    user_id = update.effective_user.id
    message = update.effective_message
    
    # **۱. بررسی لیست سیاه (Global Check)**
    if is_user_blacklisted(user_id):
        await update.message.reply_text("🚫 شما از استفاده از این ربات مسدود شده‌اید.")
        return
    
    # **۲. بررسی حالت Forwarding State (Text) - اولویت بالا برای کاربران عادی**
    if context.user_data.get('waiting_for_forward') == True and user_id != ADMIN_ID:
        # اگر پیام متنی کاربر یکی از دکمه‌های منو نبود، آن را ارسال کن.
        if text not in ["✉️ ارسال پیام به گروه فرانس فوتبال", "🏆 رتبه بندی توپ طلا", "بازگشت به منوی اصلی /start"]:
             await perform_forwarding(update, context, message)
             return
         
    # **۳. بررسی دکمه‌های منوی اصلی (همه کاربران)**
    if text == "✉️ ارسال پیام به گروه فرانس فوتبال":
        context.user_data.clear()
        context.user_data['waiting_for_forward'] = True # فعال کردن حالت فوروارد
        await update.message.reply_text("پیام خود را به صورت مستقیم ارسال کنید. پیام شما به صورت **کاملاً ناشناس** به گروه فرانس فوتبال (ادمین‌ها) ارسال خواهد شد.")
        return
        
    elif text == "🏆 رتبه بندی توپ طلا":
        context.user_data.clear()
        await send_gold_ball_rank(update, context)
        return
        
    elif text == "/rank ⚙️" and user_id == ADMIN_ID:
        await rank_command(update, context) 
        return
        
    elif text == "/blacklist 🚫" and user_id == ADMIN_ID:
        await blacklist_command(update, context)
        return
        
    elif text == "بازگشت به منوی اصلی /start":
         await start_command(update, context) 
         return
    
    # **۴. منطق مدیریت لیست سیاه (فقط ادمین)**
    blacklist_state = context.user_data.get('blacklist_state')

    if user_id == ADMIN_ID and blacklist_state:
        blacklist = load_blacklist()
        
        if text == "➕ افزودن آیدی به لیست سیاه":
            context.user_data['blacklist_state'] = 'add'
            await update.message.reply_text("✅ لطفاً **آیدی عددی** کاربری را که می‌خواهید مسدود کنید، ارسال نمایید.")
            return

        elif text == "➖ حذف آیدی از لیست سیاه":
            context.user_data['blacklist_state'] = 'remove'
            await update.message.reply_text("❌ لطفاً **آیدی عددی** کاربری را که می‌خواهید از مسدودی خارج کنید، ارسال نمایید.")
            return

        elif text == "👁️ مشاهده لیست سیاه فعلی":
            if not blacklist:
                result_text = "لیست سیاه فعلاً خالی است. 🎉"
            else:
                result_text = "کاربران مسدود شده (آیدی‌ها):\n\n" + "\n".join(f"- `{uid}`" for uid in blacklist)
            await update.message.reply_text(result_text, parse_mode='Markdown', reply_markup=get_blacklist_keyboard())
            context.user_data['blacklist_state'] = 'main'
            return

        elif blacklist_state == 'add':
            try:
                new_user_id = str(int(text.strip()))
                blacklist.add(new_user_id)
                save_blacklist(blacklist)
                await update.message.reply_text(f"کاربر با آیدی `{new_user_id}` با موفقیت **به لیست سیاه اضافه شد**.",
                                                parse_mode='Markdown', reply_markup=get_blacklist_keyboard())
            except ValueError:
                await update.message.reply_text("⛔️ آیدی عددی نامعتبر است. لطفاً فقط یک عدد صحیح وارد کنید.")
            context.user_data['blacklist_state'] = 'main'
            return

        elif blacklist_state == 'remove':
            try:
                user_to_remove = str(int(text.strip()))
                if user_to_remove in blacklist:
                    blacklist.remove(user_to_remove)
                    save_blacklist(blacklist)
                    await update.message.reply_text(f"کاربر با آیدی `{user_to_remove}` با موفقیت **از لیست سیاه حذف شد**.",
                                                    parse_mode='Markdown', reply_markup=get_blacklist_keyboard())
                else:
                    await update.message.reply_text(f"آیدی `{user_to_remove}` در لیست سیاه وجود ندارد.",
                                                    parse_mode='Markdown', reply_markup=get_blacklist_keyboard())
            except ValueError:
                await update.message.reply_text("⛔️ آیدی عددی نامعتبر است. لطفاً فقط یک عدد صحیح وارد کنید.")
            context.user_data['blacklist_state'] = 'main'
            return

    # **۵. منطق مدیریت محتوای رتبه بندی (فقط ادمین)**
    
    # Admin Confirmation State (Clearing Rank)
    if user_id == ADMIN_ID and context.user_data.get('confirm_clear') == True:
        if text in ["✅ بله، پاک شود", "❌ خیر، لغو شود"]:
            if text == "✅ بله، پاک شود":
                clear_content()
                await update.message.reply_text("🗑️ محتوای رتبه بندی توپ طلا با موفقیت **پاک شد**.", reply_markup=get_main_keyboard(True))
            else:
                await update.message.reply_text("عملیات پاک کردن لغو شد.", reply_markup=get_main_keyboard(True))
            context.user_data.clear() # پاک کردن حالت ها
            return

    # Admin Action State (Choosing save/clear)
    if user_id == ADMIN_ID and context.user_data.get('waiting_for_rank_action'):
        if text in ["➕ ذخیره‌ی محتوای جدید", "🗑️ پاک کردن محتوای فعلی"]:
            context.user_data['waiting_for_rank_action'] = False

            if text == "➕ ذخیره‌ی محتوای جدید":
                await update.message.reply_text("✅ لطفا **عکس یا متنی** که می‌خواهید به عنوان محتوای رتبه بندی توپ طلا ذخیره شود، ارسال کنید.")
                context.user_data['waiting_for_rank_content'] = True
                return
            
            elif text == "🗑️ پاک کردن محتوای فعلی":
                if load_content() is None:
                    await update.message.reply_text("🚫 محتوایی برای پاک کردن وجود ندارد.", reply_markup=get_main_keyboard(True))
                    return

                keyboard = [[KeyboardButton("✅ بله، پاک شود"), KeyboardButton("❌ خیر، لغو شود")]]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                await update.message.reply_text("⚠️ **هشدار:** آیا مطمئن هستید که می‌خواهید محتوای رتبه بندی فعلی را پاک کنید؟", reply_markup=reply_markup)
                context.user_data['confirm_clear'] = True
                return
    
    # Admin Content Saving (Text)
    if user_id == ADMIN_ID and context.user_data.get('waiting_for_rank_content'):
        if text.startswith('/'):
            await update.message.reply_text("دستورات در حالت ذخیره‌سازی محتوا قابل استفاده نیستند. لطفاً متن یا عکس رتبه‌بندی را ارسال کنید.", reply_markup=get_main_keyboard(True))
            context.user_data.clear()
            return

        new_content = {'type': 'text', 'data': text}
        save_content(new_content)
        context.user_data.clear()
        await update.message.reply_text("⭐ محتوای رتبه بندی توپ طلا با موفقیت **ذخیره شد** و دائمی است!", reply_markup=get_main_keyboard(True))
        return

    # **۶. پیام راهنما (Final Fallback)**
    if user_id != ADMIN_ID:
        await update.message.reply_text(
            "لطفاً یکی از گزینه‌های منو را انتخاب کنید. برای ارسال پیام، ابتدا دکمه '✉️ ارسال پیام به گروه فرانس فوتبال' را بزنید."
        )
        return

    pass # نادیده گرفتن پیام های ادمین که در حالت خاصی نیستند

# --- توابع کمکی ---

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """وضعیت محتوای رتبه بندی ذخیره شده را نمایش می دهد (فقط ادمین)."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("شما اجازه استفاده از این دستور را ندارید.")
        return

    content = load_content()
    
    if content is None:
        await update.message.reply_text("وضعیت: 🛑 محتوای رتبه بندی تنظیم نشده است.")
    else:
        status_text = f"وضعیت: ✅ محتوا تنظیم شده است.\nنوع: **{content['type']}**"
        
        if content['type'] == 'text':
             status_text += f"\nمحتوا (۲۰ کاراکتر اول): `{content['data'][:20]}...`"
        elif content['type'] == 'photo':
            status_text += f"\nآیدی فایل عکس: `{content['data']}`"

        await update.message.reply_text(status_text, parse_mode='Markdown')

async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """به محض ورود کاربر جدید به گروه، به او پیام خوشامدگویی در پیوی می دهد."""
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        
        # اگر کاربر جدید در لیست سیاه باشد، پیام خوشامدگویی به پیوی او ارسال نمی شود
        if is_user_blacklisted(member.id):
             print(f"User {member.id} is blacklisted and will not receive a welcome message.")
             continue
            
        try:
            welcome_message = (
                f"سلام {member.full_name}! 👋\n"
                f"به گروه خوش آمدید.\n"
                f"اگر می‌خواهید پیامی به مدیر (ادمین) بفرستید، می‌توانید در **پیوی همین ربات** پیام دهید.\n"
                f"پیام شما به صورت ناشناس در گروه نمایش داده می‌شود."
            )
            await context.bot.send_message(chat_id=member.id, text=welcome_message)
        except telegram.error.TelegramError as e:
            print(f"Cannot send private welcome message to {member.id}: {e}")


def main() -> None:
    """تابع اصلی برای اجرای ربات."""
    application = Application.builder().token(TOKEN).build()

    # --- هندلرها (Handlers) ---
    
    # 1. هندلرهای دستورات
    application.add_handlers([
        CommandHandler("start", start_command),
        CommandHandler("rank", rank_command, filters=filters.User(ADMIN_ID)), 
        CommandHandler("blacklist", blacklist_command, filters=filters.User(ADMIN_ID)), # دستور جدید لیست سیاه
        CommandHandler("status", status_command, filters=filters.User(ADMIN_ID)) 
    ])
    
    # 2. هندلر پیام‌های متنی در پیوی
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_private_text_messages))
    
    # 3. هندلر پیام‌های غیرمتنی در پیوی
    application.add_handler(MessageHandler(~filters.TEXT & filters.ChatType.PRIVATE, handle_private_non_text_messages))

    # 4. هندلر خوشامدگویی به عضو جدید
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))

    
    # اجرای ربات
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
