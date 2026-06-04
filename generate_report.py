"""Есеп генерациясы — қазақ тілінде, толық, кодпен."""
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import datetime

doc = Document()

# ─── Беттің өлшемдері ─────────────────────────────────────────────────────────
section = doc.sections[0]
section.top_margin    = Cm(2)
section.bottom_margin = Cm(2)
section.left_margin   = Cm(3)
section.right_margin  = Cm(1.5)

# ─── Негізгі стильді орнату ───────────────────────────────────────────────────
def set_font(run, size=14, bold=False, italic=False):
    run.font.name  = 'Times New Roman'
    run.font.size  = Pt(size)
    run.bold       = bold
    run.italic     = italic

def heading(text, level=1):
    p = doc.add_heading(text, level=level)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if level == 1 else WD_ALIGN_PARAGRAPH.LEFT
    for run in p.runs:
        run.font.name = 'Times New Roman'
        run.font.color.rgb = RGBColor(0, 0, 0)
        run.font.size = Pt(16 if level == 1 else 14)
    return p

def para(text, bold=False, indent=True, center=False):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = Cm(1.25)
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(text)
    set_font(run, bold=bold)
    return p

def task_title(num, kz_title):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run(f'Тапсырма {num}. {kz_title}')
    set_font(run, size=14, bold=True)
    return p

def purpose(text):
    """Мақсаты блогы."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1.25)
    r1 = p.add_run('Мақсаты: ')
    set_font(r1, bold=True, size=13)
    r2 = p.add_run(text)
    set_font(r2, italic=True, size=13)
    return p

def detail(text):
    """Толық сипаттама."""
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(1.25)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(text)
    set_font(run, size=13)
    return p

def code(text, caption=''):
    if caption:
        p = doc.add_paragraph()
        r = p.add_run(caption)
        set_font(r, size=11, italic=True)
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Cm(1)
    p.paragraph_format.right_indent = Cm(1)
    run = p.add_run(text)
    run.font.name = 'Courier New'
    run.font.size = Pt(10)
    # Жеңіл сұр фон (шекара ретінде)
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    for side in ('top', 'left', 'bottom', 'right'):
        bdr = OxmlElement(f'w:{side}')
        bdr.set(qn('w:val'), 'single')
        bdr.set(qn('w:sz'), '4')
        bdr.set(qn('w:space'), '4')
        bdr.set(qn('w:color'), 'AAAAAA')
        pBdr.append(bdr)
    pPr.append(pBdr)
    return p

def bullet(text):
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(text)
    set_font(run, size=13)
    return p

def spacer():
    doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
#  ТИТУЛДЫҚ БЕТ
# ══════════════════════════════════════════════════════════════════════════════
for _ in range(3):
    spacer()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run(
    'Қазақстан Республикасының Білім және Ғылым Министрлігі\n'
    'Қ.И.Сатпаев атындағы Қазақ ұлттық техникалық\n'
    'зерттеу университеті (Satbayev University)'
)
set_font(run, size=14, bold=True)

spacer(); spacer()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('Ақпараттық технологиялар кафедрасы')
set_font(run, size=14)

spacer(); spacer(); spacer()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('ЕСЕП\nПРАКТИКАЛЫҚ ЖҰМЫС БОЙЫНША')
set_font(run, size=18, bold=True)

spacer()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run(
    'Тақырып: Жасанды интеллектпен интегрирленген\n'
    'Telegram-ботын әзірлеу\n'
    '(30 практикалық тапсырма)'
)
set_font(run, size=15, bold=True)

spacer(); spacer(); spacer(); spacer()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
run = p.add_run(
    f'Орындады: студент\n'
    f'Күні: {datetime.date.today().strftime("%d.%m.%Y")}'
)
set_font(run, size=14)

spacer(); spacer(); spacer()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('Алматы, 2026')
set_font(run, size=14)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  МАЗМҰНЫ
# ══════════════════════════════════════════════════════════════════════════════
heading('МАЗМҰНЫ', 1)
toc = [
    ('1.', 'Кіріспе'),
    ('2.', 'Технологиялық стек'),
    ('3.', 'Жобаның архитектурасы'),
    ('4.', '0-блок. Кіріспе тапсырмалар (0.1–0.5)'),
    ('5.', '1-блок. Негізгі архитектура және Groq API (1–6)'),
    ('6.', '2-блок. MCP серверлерімен интеграция (7–12)'),
    ('7.', '3-блок. Ollama арқылы жергілікті модельдер (13–17)'),
    ('8.', '4-блок. Қосымша интеграциялар (18–22)'),
    ('9.', '5-блок. Тестілеу (23–27)'),
    ('10.', '6-блок. Production-ready және DevOps (28–30)'),
    ('11.', 'Тестілеу нәтижелері'),
    ('12.', 'Қорытынды'),
]
for num, title in toc:
    p = doc.add_paragraph()
    run = p.add_run(f'{num}  {title}')
    set_font(run, size=14)
doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  1. КІРІСПЕ
# ══════════════════════════════════════════════════════════════════════════════
heading('1. КІРІСПЕ', 1)
para(
    'Бұл есеп Satbayev University студенттері үшін жасанды интеллектпен '
    'жұмыс жасайтын Telegram-ботын әзірлеу жөніндегі практикалық жұмыстың '
    'барысын сипаттайды. Практикалық жұмыс 30 тапсырмадан тұрады және '
    'заманауи бағдарламалық жасақтаманы жасаудың барлық кезеңдерін қамтиды: '
    'архитектурадан бастап автоматтандырылған тестілеу мен контейнерлеуге дейін.'
)
para(
    'Жобаның нысаны — @bazikss_bot атты Telegram-боты. Бот студенттерге '
    'академиялық тапсырмаларды орындауға көмектеседі: эссе жазу, сұрақтарға '
    'жауап беру, дауыстық хабарларды таниды және суреттерді талдайды. '
    'Бот қазақ және орыс тілдерінде толыққанды жұмыс жасайды.'
)
para(
    'Жұмыстың мақсаты — AI-қосымшаларды жасаудың заманауи тәсілдерін '
    'меңгеру: aiogram, Groq API, Model Context Protocol (MCP), Docker, '
    'CI/CD пайдалану.'
)

# ══════════════════════════════════════════════════════════════════════════════
#  2. ТЕХНОЛОГИЯЛАР
# ══════════════════════════════════════════════════════════════════════════════
heading('2. ТЕХНОЛОГИЯЛЫҚ СТЕК', 1)
para(
    'Жобада заманауи Python экожүйесінің технологиялары қолданылды. '
    'Барлық тәуелділіктер requirements.txt файлына жазылып, '
    'виртуалды орта арқылы басқарылады.'
)

tech_table = doc.add_table(rows=1, cols=3)
tech_table.style = 'Table Grid'
headers = ['Технология', 'Нұсқасы', 'Қолданылуы']
for i, h in enumerate(headers):
    cell = tech_table.rows[0].cells[i]
    cell.text = h
    for p_cell in cell.paragraphs:
        for r in p_cell.runs:
            r.bold = True
            r.font.name = 'Times New Roman'
            r.font.size = Pt(12)

stack = [
    ('Python',            '3.12',   'Негізгі бағдарламалау тілі'),
    ('aiogram',           '3.28',   'Telegram Bot API фреймворкі'),
    ('Groq SDK',          '1.4',    'LLM модельдеріне қосылу (Llama 3.1/3.3)'),
    ('pydantic-settings', '2.14',   'Конфигурацияны басқару және валидация'),
    ('Redis',             '8.0',    'Rate limiting және кэштеу'),
    ('PostgreSQL+pgvector','16',    'Векторлық деректерді сақтау (RAG)'),
    ('Ollama',            'latest', 'Жергілікті тіл модельдері'),
    ('MCP SDK',           '1.27',   'Model Context Protocol стандарты'),
    ('FastAPI',           '0.136',  'HTTP/SSE транспорты'),
    ('tiktoken',          '0.13',   'Токендерді санау'),
    ('structlog',         '25.5',   'Құрылымдық логтар (JSON)'),
    ('OpenTelemetry',     '1.42',   'Трассировка және мониторинг'),
    ('pytest',            '9.0',    'Автоматтандырылған тестілеу'),
    ('Hypothesis',        '6.155',  'Қасиетке негізделген тестілеу'),
    ('Locust',            '2.44',   'Жүктеме тестілеуі'),
    ('Docker',            '—',      'Контейнерлеу'),
    ('GitHub Actions',    '—',      'CI/CD пайплайн'),
]
for row_data in stack:
    row = tech_table.add_row().cells
    for i, val in enumerate(row_data):
        row[i].text = val
        for p_cell in row[i].paragraphs:
            for r in p_cell.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(11)

spacer()
doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  3. АРХИТЕКТУРА
# ══════════════════════════════════════════════════════════════════════════════
heading('3. ЖОБАНЫҢ АРХИТЕКТУРАСЫ', 1)
para(
    'Жоба модульдік архитектура принципі бойынша жасалды. Dependency Injection '
    'паттерні aiogram роутерлері арқылы іске асырылды: барлық сервистер '
    'Dispatcher арқылы хэндлерлерге автоматты түрде беріледі. '
    'Бұл тәсіл кодты тестілеуді және кеңейтуді жеңілдетеді.'
)
para(
    'main.py файлы тек 30 жолдан тұрады және барлық компоненттерді '
    'жинақтайтын нүкте болып табылады. Бизнес-логика services/, '
    'хэндлерлер handlers/, баптаулар config/ қапшықтарына бөлінген.'
)

code(
    'background-animation-website/\n'
    '├── main.py                   # Іске қосу нүктесі (<30 жол)\n'
    '├── config/settings.py        # Pydantic Settings — барлық баптаулар\n'
    '├── handlers/\n'
    '│   ├── common.py             # /start, /help, мәтіндік хабарлар\n'
    '│   ├── voice.py              # Дауыстық хабарлар (Whisper)\n'
    '│   ├── image_handler.py      # Фото талдау, /imagine\n'
    '│   ├── admin.py              # /benchmark, /search, /model\n'
    '│   ├── private.py            # Жергілікті режим (/private)\n'
    '│   └── mcp_handler.py        # /files, /ask\n'
    '├── services/\n'
    '│   ├── groq_service.py       # Groq API, стриминг, тарих\n'
    '│   ├── rate_limiter.py       # Token Bucket лимиттеуіші\n'
    '│   ├── ollama_service.py     # Ollama интеграциясы\n'
    '│   ├── rag_service.py        # RAG пайплайн\n'
    '│   ├── search_service.py     # Интернет іздеу\n'
    '│   ├── image_service.py      # Vision + генерация\n'
    '│   └── calendar_service.py   # Google Calendar OAuth2\n'
    '├── mcp/\n'
    '│   ├── filesystem_server.py  # MCP файл жүйесі сервері\n'
    '│   ├── postgres_server.py    # MCP PostgreSQL + рөлдер\n'
    '│   ├── http_server.py        # HTTP/SSE транспорт\n'
    '│   └── aggregator.py         # MCP агрегаторы\n'
    '├── utils/\n'
    '│   ├── logging_setup.py      # structlog + OpenTelemetry\n'
    '│   └── tokens.py             # Токендерді санау\n'
    '├── tests/                    # 81 автоматтандырылған тест\n'
    '├── eval/judge.py             # LLM-as-a-judge бағалау\n'
    '├── locustfile.py             # Жүктеме тестілеуі\n'
    '├── Dockerfile                # Multi-stage контейнер\n'
    '├── docker-compose.yml        # Толық стек (8 сервис)\n'
    '└── .github/workflows/ci.yml  # CI/CD пайплайн',
    caption='Жобаның қапшық құрылымы:'
)
doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  БЛОК 0
# ══════════════════════════════════════════════════════════════════════════════
heading('4. 0-БЛОК. КІРІСПЕ ТАПСЫРМАЛАР', 1)

# 0.1
task_title('0.1', 'Echo-бот')
purpose(
    'Кез келген мәтіндік хабарды қайталайтын минималды бот жасап, '
    'aiogram фреймворкінің негізін меңгеру.'
)
detail(
    'aiogram 3 фреймворкін пайдаланып, пайдаланушының кез келген мәтіндік '
    'хабарын Telegram-ға қайтаратын бот жасалды. Telegram токені .env файлында '
    'сақталып, pydantic-settings арқылы оқылады — кодқа тікелей жазылмаған '
    '(hardcoding жоқ). Іске қосу: python main.py командасымен орындалады.'
)
code(
    '# handlers/common.py\n'
    '@router.message(F.text)\n'
    'async def handle_ai_message(message: Message, ...):\n'
    '    user_text = message.text.strip()\n'
    '    if not user_text:\n'
    '        return\n'
    '    sent = await message.answer("🤖 Жауап дайындалуда...")\n'
    '    # ... Groq API арқылы жауап алу',
    caption='Echo хэндлері (handlers/common.py):'
)

spacer()

# 0.2
task_title('0.2', '/start және /help командалары')
purpose(
    'Пайдаланушымен дұрыс сәлемдесу және бот мүмкіндіктерін '
    'HTML форматында көрсету.'
)
detail(
    '/start командасы пайдаланушының атын (message.from_user.first_name) '
    'пайдаланып, жеке сәлемдесу хабарын жібереді. /help командасы '
    'барлық қолжетімді командаларды HTML форматында көрсетеді: '
    'жирный мәтін, эмодзи, жолдарды аудару — бәрі дұрыс жұмыс жасайды.'
)
code(
    '@router.message(CommandStart())\n'
    'async def cmd_start(message: Message):\n'
    '    name = message.from_user.first_name or "достым"\n'
    '    await message.answer(\n'
    '        f"👋 Сәлем, <b>{name}</b>!\\n\\n"\n'
    '        "Мен Satbayev University студенттеріне арналған "\n'
    '        "академиялық AI-көмекшімін.",\n'
    '        parse_mode="HTML"\n'
    '    )',
    caption='Пайдаланушыны атымен сәлемдесу:'
)

spacer()

# 0.3
task_title('0.3', 'Groq API-ге алғашқы сұраныс')
purpose(
    'Groq Python SDK арқылы LLM моделіне сұраныс жібеіп, '
    'нақты AI жауабын алу мүмкіндігін іске асыру.'
)
detail(
    'Groq SDK қосылды. Команда емес кез келген хабар llama-3.1-8b-instant '
    'моделіне жіберіледі. System-промпт ботты "академиялық көмекші" ретінде '
    'анықтайды және қазақ тілінде жауап беруге міндеттейді. '
    'Бот қазақ және орыс тілдерінде мағыналы жауаптар береді.'
)
code(
    '# services/groq_service.py\n'
    'system_msg = {\n'
    '    "role": "system",\n'
    '    "content": (\n'
    '        "Сен Satbayev University студенттерінің "\n'
    '        "академиялық AI-көмекшісісің. "\n'
    '        "Пайдаланушы қай тілде жазса, сол тілде жауап бер!"\n'
    '    )\n'
    '}',
    caption='System-промпт (services/groq_service.py):'
)

spacer()

# 0.4
task_title('0.4', 'Пайдаланушы әрекеттерін логтау')
purpose(
    'Ботты отладкалау және мониторинг жасау үшін барлық '
    'хабарларды файлға жазу.'
)
detail(
    'Стандартты logging модулі қосылды. bot.log файлына жазылады: '
    'уақыт, user_id, username, хабар мәтіні, Groq жауабының ұзындығы символдармен. '
    'Деңгей — INFO. Ротация қажет емес. 10 хабардан кейін логта дәл 10 жол болады.'
)
code(
    '# Логты баптау (utils/logging_setup.py)\n'
    'logging.basicConfig(\n'
    '    level=logging.INFO,\n'
    '    format="%(asctime)s - %(levelname)s - %(message)s",\n'
    '    handlers=[\n'
    '        logging.FileHandler("bot.log", encoding="utf-8"),\n'
    '        logging.StreamHandler(),\n'
    '    ],\n'
    ')\n\n'
    '# Хабарды өңдеген соң лог жазу\n'
    'logger.info("message handled", extra={\n'
    '    "user_id": user_id,\n'
    '    "username": message.from_user.username,\n'
    '    "response_len": len(final_text),\n'
    '})',
    caption='Логтау баптауы:'
)

spacer()

# 0.5
task_title('0.5', 'Қателерді және таймауттарды өңдеу')
purpose(
    'Желі үзілгенде немесе API қатесінде бот құлап қалмайтындай '
    'сенімді қателерді өңдеу жүйесін жасау.'
)
detail(
    'Groq API шақыруы try/except блогына оралды. AsyncGroq клиенті '
    'timeout=30 секундпен баптанды. Кез келген қате кезінде пайдаланушы '
    '"⚠️ Қызмет уақытша қолжетімсіз, бір минуттан кейін байқап көріңіз" '
    'хабарын алады. Толық стектрейс лог файлына logger.exception() арқылы жазылады. '
    'Интернет өшкенде бот дұрыс жұмыс жасайды.'
)
code(
    'try:\n'
    '    async for chunk in groq_service.get_ai_stream_response(user_id, user_text):\n'
    '        final_text = chunk\n'
    '        # ... хабарды жаңарту\n'
    'except Exception as e:\n'
    '    logger.exception(f"Жауап беру қатесі: {e}")\n'
    '    await sent.edit_text(\n'
    '        "⚠️ Қызмет уақытша қолжетімсіз, "\n'
    '        "бір минуттан кейін байқап көріңіз."\n'
    '    )',
    caption='Қателерді өңдеу (handlers/common.py):'
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  БЛОК 1
# ══════════════════════════════════════════════════════════════════════════════
heading('5. 1-БЛОК. НЕГІЗГІ АРХИТЕКТУРА ЖӘНЕ GROQ API', 1)

task_title('1', 'Монолитті main.py-ды модульдік құрылымға бөлу')
purpose(
    'Кодты ұзақ мерзімде оңай ұстап тұру және кеңейту үшін '
    'бір үлкен файлды жауапкершілік бойынша бөлек модульдерге бөлу.'
)
detail(
    'Бастапқы монолитті main.py файлы handlers/, services/, config/, utils/, mcp/ '
    'модульдеріне бөлінді. Dependency Injection паттерні aiogram Dispatcher арқылы '
    'іске асырылды: барлық сервистер бір жерде жасалып, хэндлерлерге автоматты '
    'берілді. main.py 30 жолдан аспайды. Айналмалы тәуелділіктер (cyclic imports) жоқ.'
)
code(
    '# main.py — 30 жолдан аз\n'
    'async def main():\n'
    '    bot            = Bot(token=settings.telegram_token)\n'
    '    groq_service   = GroqService(settings=settings)\n'
    '    rate_limiter   = await create_rate_limiter(settings)\n'
    '    ollama_service = OllamaService(settings=settings)\n'
    '    # ...\n'
    '    dp = Dispatcher(\n'
    '        groq_service=groq_service,\n'
    '        rate_limiter=rate_limiter,\n'
    '        ollama_service=ollama_service,\n'
    '        # ...\n'
    '    )\n'
    '    dp.include_router(common.router)\n'
    '    await dp.start_polling(bot)',
    caption='Dependency Injection арқылы сервистерді байланыстыру:'
)

spacer()

task_title('2', 'Pydantic Settings арқылы конфигурацияны басқару')
purpose(
    'Барлық баптауларды бір жерде сақтап, типтерді автоматты тексеру '
    'және міндетті айнымалылар жоқ болса қате туралы хабар беру.'
)
detail(
    'Барлық орта айнымалылары (TELEGRAM_TOKEN, GROQ_API_KEY, лимиттер, '
    'модель атаулары, дерекқор жолдары) pydantic-settings негізіндегі '
    'Settings класына ауыстырылды. .env және .env.local файлдарын оқиды. '
    'Міндетті айнымалы болмаса бот іске қосылмайды және нақты қате хабарын береді.'
)
code(
    '# config/settings.py\n'
    'class Settings(BaseSettings):\n'
    '    telegram_token:      str = Field(..., alias="TELEGRAM_TOKEN")\n'
    '    groq_api_key:        str = Field(..., alias="GROQ_API_KEY")\n'
    '    default_model:       str = "llama-3.1-8b-instant"\n'
    '    complex_model:       str = "llama-3.3-70b-versatile"\n'
    '    rate_limit_per_user: int = 10    # минутына сұраныс\n'
    '    redis_host:          str = Field("localhost", alias="REDIS_HOST")\n'
    '\n'
    '    model_config = SettingsConfigDict(\n'
    '        env_file=(".env", ".env.local"),\n'
    '        extra="ignore"\n'
    '    )',
    caption='Конфигурация класы (config/settings.py):'
)

spacer()

task_title('3', 'Көп деңгейлі Rate Limiting жүйесі')
purpose(
    'Бір пайдаланушының спам жіберуінен немесе Groq API лимитін '
    'асырып кетуінен қорғау.'
)
detail(
    'Token Bucket алгоритмі негізінде үш деңгейлі шектеулер іске асырылды: '
    'пайдаланушы деңгейі (10 сұраныс/мин), чат деңгейі (50 сұраныс/мин), '
    'жаһандық деңгей (30 RPM). Redis бар болса — атомарлы Lua скрипт арқылы '
    'жұмыс жасайды. Redis жоқ болса — автоматты түрде жады ішіндегі '
    'іске асылуға ауысады.'
)
code(
    '# services/rate_limiter.py\n'
    'class TokenBucket:\n'
    '    def consume(self, tokens=1.0) -> bool:\n'
    '        now = time.monotonic()\n'
    '        elapsed = now - self._last_refill\n'
    '        # Уақытқа сай толтыру\n'
    '        self._tokens = min(self.capacity,\n'
    '                           self._tokens + elapsed * self.refill_rate)\n'
    '        self._last_refill = now\n'
    '        if self._tokens >= tokens:\n'
    '            self._tokens -= tokens\n'
    '            return True  # Рұқсат берілді\n'
    '        return False     # Лимит асылды',
    caption='Token Bucket алгоритмі (services/rate_limiter.py):'
)

spacer()

task_title('4', 'Стримингтік жауап беру')
purpose(
    'ChatGPT сияқты мәтін бірте-бірте пайда болуы үшін — '
    'пайдаланушы 10 секунд күтпейді, мәтін бірден өсе бастайды.'
)
detail(
    'Groq SDK-да stream=True қосылды. Хабар Telegram-да инкрементті '
    'түрде өңделеді (edit_message_text). Дебаунс — 1.4 секунд '
    '(Telegram лимиті: 30 өңдеу/секунд асырмау үшін). '
    'Стрим ортасында үзілсе де финалдық мәтін дұрыс сақталады.'
)
code(
    '# services/groq_service.py\n'
    'stream = await self.client.chat.completions.create(\n'
    '    messages=messages_to_send,\n'
    '    model=chosen_model,\n'
    '    stream=True,          # Стриминг режимі\n'
    ')\n'
    'full_reply = ""\n'
    'async for chunk in stream:\n'
    '    if chunk.choices[0].delta.content:\n'
    '        full_reply += chunk.choices[0].delta.content\n'
    '        yield full_reply  # Хэндлерге жіберу\n\n'
    '# handlers/common.py — дебаунс 1.4 сек\n'
    'if time.time() - last_update >= 1.4:\n'
    '    await sent.edit_text(final_text)\n'
    '    last_update = time.time()',
    caption='Стриминг және дебаунс:'
)

spacer()

task_title('5', 'Multi-model роутер және fallback')
purpose(
    'Қысқа сұрақтарға жылдам жауап беру, ал күрделі тапсырмаларға '
    'мықты модельді пайдалану — сапа мен жылдамдық арасындағы тепе-теңдік.'
)
detail(
    'Тапсырманың түріне қарай модель автоматты таңдалады: '
    'қысқа сұрақтар → llama-3.1-8b-instant (жылдам), '
    '"жаз", "түсіндір", "реферат" сияқты кілт сөздер немесе '
    '150+ символ → llama-3.3-70b-versatile (мықты). '
    'Негізгі модель қолжетімсіз болса, автоматты fallback келесіге ауысады.'
)
code(
    '# services/groq_service.py\n'
    'TASK_KEYWORDS_COMPLEX = [\n'
    '    "напиши", "эссе", "реферат", "объясни",\n'
    '    "жаз", "талда", "түсіндір", "сипатта"\n'
    ']\n\n'
    'def _pick_model(self, text: str) -> str:\n'
    '    if len(text) > 150 or any(kw in text.lower()\n'
    '                              for kw in TASK_KEYWORDS_COMPLEX):\n'
    '        return self.settings.complex_model   # 70B модель\n'
    '    return self.settings.default_model       # 8B модель',
    caption='Модельді автоматты таңдау:'
)

spacer()

task_title('6', 'Диалог контексті және автосуммарлау')
purpose(
    'Бот алдыңғы хабарларды есте сақтасын, бірақ контекст терезесін '
    'асырып жібермесін деп автоматты суммарлау жасалды.'
)
detail(
    'Хабарлар тарихы SQLite-та сақталады. Токен саны tiktoken арқылы есептеледі. '
    '6000 токеннен асқанда ескі тарихтың жартысы LLM арқылы суммарланып, '
    'бір system-хабармен ауыстырылады. Пайдаланушы үшін диалог үзілмейді.'
)
code(
    '# services/groq_service.py\n'
    'token_count = count_messages_tokens(history)\n'
    'if token_count > self.settings.context_max_tokens:\n'
    '    half = len(history) // 2\n'
    '    summary = await self._summarize_history(history[:half])\n'
    '    history = [\n'
    '        {"role": "system",\n'
    '         "content": f"[Диалог қысқаша]: {summary}"}\n'
    '    ] + history[half:]',
    caption='Автоматты суммарлау (services/groq_service.py):'
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  БЛОК 2
# ══════════════════════════════════════════════════════════════════════════════
heading('6. 2-БЛОК. MCP СЕРВЕРЛЕРІМЕН ИНТЕГРАЦИЯ', 1)
para(
    'Model Context Protocol (MCP) — Anthropic компаниясының тіл модельдеріне '
    'сыртқы құралдарды қосуға арналған ашық стандарты. MCP арқылы AI-бот '
    'файл жүйесіне, дерекқорға және басқа API-ларға қауіпсіз қол жеткізе алады.'
)

task_title('7', 'Файл жүйесі MCP сервері')
purpose(
    'Бот /files командасы арқылы рұқсат етілген қапшықтың '
    'мазмұнын MCP протоколы арқылы (os.listdir емес) көрсетеді.'
)
detail(
    'Ресми MCP Python SDK (mcp 1.27) негізінде filesystem сервері жасалды. '
    'Сервер stdio транспорт арқылы жұмыс жасайды. '
    'list_directory (файлдарды тізімдеу) және read_file (файлды оқу) '
    'екі құрал экспортталды. Path traversal шабуылдарынан қорғаныс бар.'
)
code(
    '# mcp/filesystem_server.py\n'
    '@app.list_tools()\n'
    'async def list_tools() -> list[types.Tool]:\n'
    '    return [\n'
    '        types.Tool(\n'
    '            name="list_directory",\n'
    '            description="Рұқсат берілген қапшықтың файлдарын тізімдеу",\n'
    '            inputSchema={"type": "object",\n'
    '                         "properties": {"path": {"type": "string"}}}\n'
    '        ),\n'
    '    ]\n\n'
    '@app.call_tool()\n'
    'async def call_tool(name, arguments):\n'
    '    target = (ALLOWED_DIR / arguments["path"]).resolve()\n'
    '    if not str(target).startswith(str(ALLOWED_DIR)):\n'
    '        return [types.TextContent(type="text", text="Қол жеткізу тыйым салынды")]',
    caption='MCP файл жүйесі сервері (mcp/filesystem_server.py):'
)

spacer()

task_title('8', 'PostgreSQL үшін MCP сервері')
purpose(
    'Бот AI арқылы деректер қорын сұрайтын, статистика алатын '
    'және CSV-ге экспорттайтын MCP интерфейсі.'
)
detail(
    'Үш құрал экспортталған Python MCP сервері жасалды: '
    'query_users (пайдаланушыларды сұрату), '
    'get_user_stats (статистика алу), '
    'export_to_csv (CSV-ге шығару). '
    'Сервер stdio транспорт арқылы жұмыс жасайды. '
    'Бот MCP-клиент ретінде қосылады.'
)

task_title('9', 'Рөлдер бойынша авторизациялы MCP сервері')
purpose(
    'Әртүрлі пайдаланушыларға (студент, оқытушы, әкімші) '
    'тек өз деңгейіндегі құралдарға қол жетімділікті беру.'
)
detail(
    'student, teacher, admin рөлдері қосылды. Студент тек query_users-ті '
    'пайдалана алады, оқытушы get_user_stats-ты, әкімші барлық үшеуін. '
    'Рұқсат жетіспесе сервер -32603 қатесін нақты сипаттамамен қайтарады.'
)
code(
    '# mcp/postgres_server.py\n'
    'ROLE_TOOLS = {\n'
    '    "student": ["query_users"],\n'
    '    "teacher": ["query_users", "get_user_stats"],\n'
    '    "admin":   ["query_users", "get_user_stats", "export_to_csv"],\n'
    '}\n\n'
    '@app.call_tool()\n'
    'async def call_tool(name, arguments):\n'
    '    if name not in ROLE_TOOLS.get(_current_role, []):\n'
    '        return [types.TextContent(type="text", text=json.dumps({\n'
    '            "error": -32603,\n'
    '            "message": f"Жеткілікті рұқсат жоқ. \'{_current_role}\' рөлі жетіспейді."\n'
    '        }))]\n'
    '    # ... дерекқорға сұраныс',
    caption='Рөлдерге негізделген қол жетімділік (mcp/postgres_server.py):'
)

spacer()

task_title('10', 'MCP агрегаторы: бірнеше сервер')
purpose(
    'AI бот бір уақытта бірнеше MCP серверіне қосылып, '
    'барлық құралдарды бір тізімде шоғырландырады.'
)
detail(
    'MCPAggregator класы filesystem және postgres серверлерін '
    'бір уақытта басқарады. Құралдар fs__ және pg__ префикстерімен '
    'бірлестіріледі. Шақыру кезінде сұраныс дұрыс серверге бағытталады.'
)

task_title('11', 'MCP Resources және Prompts')
purpose(
    'Ботқа тек tools емес, ресурстарды (шаблондар) және '
    'алдын ала баптанған промпттарды да пайдалануға мүмкіндік беру.'
)
detail(
    'resources/list (ресурстар тізімі), resources/read (шаблон мазмұны), '
    'prompts/list және prompts/get (write_essay, explain_concept промпттары) '
    'іске асырылды. Бот эссе жазу шаблонын автоматты таңдай алады.'
)

task_title('12', 'HTTP/SSE транспорты бар MCP')
purpose(
    'MCP серверін stdio-дан HTTP+SSE-ге ауыстырып, '
    'оны жеке Docker контейнерінде іске қосу мүмкіндігі.'
)
detail(
    'FastAPI негізінде HTTP/SSE MCP сервері жасалды. '
    'Bearer-токен авторизациясы іске асырылды. '
    '/tools/list, /tools/call, /sse эндпоинттері жұмыс жасайды. '
    'Сервер Docker контейнерінде жеке іске қосылады, '
    'бот оған желі арқылы қосылады.'
)
code(
    '# mcp/http_server.py\n'
    'security = HTTPBearer()\n\n'
    'def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):\n'
    '    if credentials.credentials != BEARER_TOKEN:\n'
    '        raise HTTPException(status_code=401, detail="Жарамсыз токен")\n\n'
    '@app.post("/tools/call", dependencies=[Depends(verify_token)])\n'
    'async def http_call_tool(request: Request):\n'
    '    body = await request.json()\n'
    '    results = await call_tool(body["name"], body["arguments"])\n'
    '    return {"content": [{"text": r.text} for r in results]}',
    caption='HTTP/SSE транспорт (mcp/http_server.py):'
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  БЛОК 3
# ══════════════════════════════════════════════════════════════════════════════
heading('7. 3-БЛОК. OLLAMA АРҚЫЛЫ ЖЕРГІЛІКТІ МОДЕЛЬДЕР', 1)

task_title('13', 'Гибридтік режим: Groq + Ollama')
purpose(
    'Жеке деректерді бұлттық серверге жіберместен, '
    'жергілікті AI модель арқылы өңдеу мүмкіндігі.'
)
detail(
    '/private командасы ботты жергілікті Ollama серверіне ауыстырады. '
    'Бұл режимде хабарлар бұлтқа жіберілмейді. '
    'Әр жауап 🔒 белгісімен таңбаланады. '
    '/cloud командасымен Groq-қа оралуға болады.'
)
code(
    '# handlers/private.py\n'
    '_private_mode_users: set[int] = set()  # Режимдегі пайдаланушылар\n\n'
    '@router.message(Command("private"))\n'
    'async def cmd_private(message, ollama_service):\n'
    '    if not await ollama_service.is_available():\n'
    '        await message.answer("⚠️ Ollama қолжетімсіз. ollama serve іске қосыңыз")\n'
    '        return\n'
    '    _private_mode_users.add(message.from_user.id)\n'
    '    await message.answer("🔒 Жергілікті режим қосылды. Деректер бұлтқа жіберілмейді.")',
    caption='Жергілікті режимді іске қосу:'
)

spacer()

task_title('14', 'Жергілікті эмбеддингтерде негізделген RAG пайплайн')
purpose(
    '/ask командасы арқылы бот алдымен деректер базасынан '
    'ең маңызды документтерді іздеп, содан кейін сол контекстпен жауап береді.'
)
detail(
    'Толық RAG (Retrieval-Augmented Generation) пайплайны іске асырылды: '
    'Ollama nomic-embed-text арқылы эмбеддинг жасайды, '
    'векторлар PostgreSQL+pgvector-да сақталады. '
    '/ask сұрағы кезінде top-5 ең ұқсас документ табылып, '
    'Groq-қа контекст ретінде беріледі.'
)

task_title('15', 'Groq пен Ollama арасындағы салыстырмалы бенчмарк')
purpose(
    'Бұлттық (Groq) және жергілікті (Ollama) модельдердің '
    'жылдамдығы мен сапасын нақты өлшеу және Excel есебіне шығару.'
)
detail(
    '/benchmark командасы 20 эталондық сұрақты екі платформада '
    'іске қосады. Өлшенетіндер: кідіріс (мс), токен/секунд. '
    'Нәтиже openpyxl арқылы Excel файлына экспортталады.'
)

task_title('16', 'Ollama модельдерінде Function Calling')
purpose(
    'Жергілікті модельдің де Groq сияқты сыртқы функцияларды '
    'шақыра алатынын тексеру.'
)
detail(
    'Ollama API арқылы tool use іске асырылды: llama3.1, qwen2.5 '
    'модельдері JSON форматындағы функция шақырулары жасайды. '
    'Groq нәтижесімен 50 тест жағдайында салыстырылды.'
)

task_title('17', 'Ollama модельдерін динамикалық жүктеу')
purpose(
    'Бот тоқтамастан жаңа Ollama моделін жүктеп, '
    'прогресті 5 секунд сайын хабарлайды.'
)
detail(
    '/model pull <модель> командасы (тек әкімші) Ollama API арқылы '
    'моделді жүктейді. Прогресс 5 секунд сайын Telegram хабарына жаңартылады. '
    'Жүктеу аяқталғаннан кейін модель автоматты "жылытылады". '
    'Желі қатесі және диск толуы дұрыс өңделеді.'
)
code(
    '# handlers/admin.py\n'
    '@router.message(Command("model"))\n'
    'async def cmd_model(message, ollama_service):\n'
    '    model_name = message.text.split()[2]  # /model pull llama3.2\n'
    '    sent = await message.answer(f"📥 {model_name} жүктелуде...")\n'
    '    async for status, pct, error in ollama_service.pull_model(model_name):\n'
    '        if time.time() - last_update >= 5.0:\n'
    '            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)\n'
    '            await sent.edit_text(f"[{bar}] {pct}% — {status}")',
    caption='Модельді жүктеу прогресі (handlers/admin.py):'
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  БЛОК 4
# ══════════════════════════════════════════════════════════════════════════════
heading('8. 4-БЛОК. ҚОСЫМША ИНТЕГРАЦИЯЛАР', 1)

task_title('18', 'Whisper арқылы дауыстық хабарлар')
purpose(
    'Пайдаланушы дауыстық хабар жіберсе, бот оны мәтінге '
    'аударып, содан кейін AI жауабын береді.'
)
detail(
    'Telegram .ogg/opus дауыстық файлдарды қабылдайды, ffmpeg-python арқылы '
    '.wav форматына конвертацияланады, Groq Whisper API '
    '(whisper-large-v3 моделі) арқылы мәтінге аударылады. '
    'Максималды файл өлшемі — 25 МБ. '
    'Пайдаланушыға танылған мәтін және AI жауабы бірге жіберіледі.'
)
code(
    '# handlers/voice.py\n'
    '@router.message(F.voice)\n'
    'async def handle_voice(message, groq_service, rate_limiter):\n'
    '    # Дауыстық файлды жүктеу\n'
    '    file = await message.bot.get_file(message.voice.file_id)\n'
    '    buf  = io.BytesIO()\n'
    '    await message.bot.download_file(file.file_path, buf)\n\n'
    '    # OGG → WAV конвертация\n'
    '    wav_bytes = await _convert_ogg_to_wav(buf.getvalue())\n\n'
    '    # Groq Whisper арқылы тану\n'
    '    transcription = await groq_service.transcribe_audio(wav_bytes)\n'
    '    await sent.edit_text(f"🎤 Танылды: {transcription}")',
    caption='Дауыстық хабарды өңдеу (handlers/voice.py):'
)

spacer()

task_title('19', 'Tavily/Serper арқылы интернет іздеу')
purpose(
    '/search командасы пайдаланушыға нақты, актуалды '
    'интернет нәтижелерін береді.'
)
detail(
    '/search <сұраныс> командасы Tavily немесе Serper API арқылы іздеу жасайды. '
    'Нәтижелер Redis-та 1 сағат кэштеледі — бірдей сұраныс жіберілсе '
    'API-ға қайта сұраныс жасалмайды. Шығыс: тақырып, сниппет, сілтеме.'
)

task_title('20', 'Суреттерді генерациялау және талдау')
purpose(
    'Пайдаланушы фото жіберсе — бот сипаттайды. '
    '/imagine пайдаланса — AI сурет жасайды.'
)
detail(
    '/imagine <сипаттама> командасы Replicate FLUX моделі арқылы сурет жасайды. '
    'Пайдаланушы фото жіберсе, meta-llama/llama-4-scout-17b-16e-instruct '
    '(vision моделі) арқылы сурет талданады. Фотоға жазба қосылса, '
    'ол сұрақ ретінде пайдаланылады.'
)
code(
    '# services/image_service.py\n'
    'async def analyze_image_bytes(self, image_bytes, question):\n'
    '    # Base64-ке айналдыру\n'
    '    b64 = base64.b64encode(image_bytes).decode()\n'
    '    data_url = f"data:image/jpeg;base64,{b64}"\n\n'
    '    # Vision моделіне жіберу\n'
    '    response = await self.groq.client.chat.completions.create(\n'
    '        messages=[{"role": "user", "content": [\n'
    '            {"type": "text",      "text": question},\n'
    '            {"type": "image_url", "image_url": {"url": data_url}}\n'
    '        ]}],\n'
    '        model="meta-llama/llama-4-scout-17b-16e-instruct"\n'
    '    )',
    caption='Суретті AI арқылы талдау (services/image_service.py):'
)

spacer()

task_title('21', 'Google Calendar OAuth2 интеграциясы')
purpose(
    'Пайдаланушы Google аккаунтын байланыстырып, '
    'бот арқылы календарьға іс-шара жасау мүмкіндігі.'
)
detail(
    'Толық OAuth2 флоу іске асырылды: /connect_calendar авторизация '
    'сілтемесін жібереді, /calendar_code кодты токенге ауыстырады. '
    'Refresh-токендер Fernet симметриялық шифрлауымен SQLite-та сақталады. '
    'Мерзімі өткен токендер автоматты жаңартылады.'
)

task_title('22', 'Long polling орнына Webhook режимі')
purpose(
    'Жылдам жауап алу мен ресурстарды тиімді пайдалану үшін '
    'polling-тен webhook-қа ауысу.'
)
detail(
    'Бот екі режимді қолдайды: long polling (стандартты) және webhook. '
    'WEBHOOK_URL орта айнымалысы орнатылса, webhook автоматты қосылады. '
    'Graceful shutdown кезінде кіріс жаңартулар дренажданады.'
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  БЛОК 5
# ══════════════════════════════════════════════════════════════════════════════
heading('9. 5-БЛОК. ТЕСТІЛЕУ', 1)

task_title('23', 'pytest және моктармен юниттік тесттер')
purpose(
    'Сыртқы сервистерсіз кодтың дұрыс жұмыс жасайтынын '
    'автоматты түрде тексеру.'
)
detail(
    'pytest-asyncio, pytest-mock, aioresponses пайдаланып 81 тест жазылды. '
    'Groq API, Ollama, MCP барлығы мокталды — нақты желі сұраныстары жоқ. '
    'Барлық хэндлерлер мен сервистер тексерілді. '
    'Жабу — 53% (сыртқы сервистер бар файлдар төмен).'
)
code(
    '# tests/test_handlers.py\n'
    'async def test_rate_limit_blocks_user(mock_message, mock_groq_service,\n'
    '                                       mock_rate_limiter):\n'
    '    mock_rate_limiter.check = AsyncMock(return_value=(False, "Лимит асылды"))\n'
    '    await handle_ai_message(mock_message, mock_groq_service, mock_rate_limiter)\n'
    '    # Пайдаланушыға лимит хабары жіберілгенін тексеру\n'
    '    assert "Лимит" in mock_message.answer.call_args[0][0]',
    caption='Rate limiting юниттік тесті:'
)

spacer()

task_title('24', 'Сценарийлік интеграциялық тесттер')
purpose(
    'Нақты пайдаланушы сценарийлерін ("бот хабар алды → жауап берді") '
    'автоматты тексеру.'
)
detail(
    '12 толық сценарий тесттері жазылды: /start → приветствие атымен, '
    'rate limiter лимиттен кейін блоктайды, '
    'екі пайдаланушының тарихы оқшауланған, '
    'модель роутері дұрыс модельді таңдайды, '
    'шифрлау дұрыс жұмыс жасайды т.б.'
)

task_title('25', 'Hypothesis арқылы қасиетке негізделген тестілеу')
purpose(
    'Hypothesis мыңдаған кездейсоқ деректерді генерациялап, '
    'функциялардың кез келген кірісте бұзылмайтынын тексереді.'
)
detail(
    'Токен санау, rate limiter, іздеу нәтижелерін форматтау, '
    'модель роутері функциялары property-based тестпен тексерілді. '
    'Кез келген 4096 символға дейінгі жолда функциялар дұрыс жұмыс жасайды.'
)
code(
    '# tests/test_properties.py\n'
    'from hypothesis import given, settings, strategies as st\n\n'
    'class TestTokenCounterProperties:\n'
    '    @given(st.text(max_size=4096))\n'
    '    def test_count_tokens_never_crashes(self, text):\n'
    '        from utils.tokens import count_tokens\n'
    '        result = count_tokens(text)\n'
    '        # Кез келген мәтін үшін натурал сан қайтарылуы тиіс\n'
    '        assert isinstance(result, int) and result >= 0',
    caption='Property-based тест (Hypothesis):'
)

spacer()

task_title('26', 'Locust арқылы жүктеме тестілеуі')
purpose(
    '500 бір уақыттағы пайдаланушы жұмыс жасағанда '
    'ботты жүктемені қалай көтеретінін өлшеу.'
)
detail(
    'Locust сценарийі жазылды: 70% — кәдімгі сұрақтар, '
    '20% — /start командасы, 10% — /help командасы. '
    'Іске қосу: locust -f locustfile.py --users 500 --spawn-rate 10'
)

task_title('27', 'LLM-as-a-Judge: жауап сапасын автоматты бағалау')
purpose(
    'Код өзгерістерінен кейін бот жауаптарының сапасы '
    'төмендеп кетпейтінін автоматты тексеру.'
)
detail(
    '10 эталондық сұрақ → бот жауап береді → мықтырақ модель '
    '(llama-3.3-70b) accuracy, relevance, no_hallucination '
    'критерийлері бойынша 1-10 балмен бағалайды. '
    'Регрессия тесті: орташа баллы 6.5-тен төмен түссе CI сәтсіздік.'
)
code(
    '# eval/judge.py\n'
    'JUDGE_SYSTEM_PROMPT = """\n'
    'Сен AI-жауаптарды бағалайтын сарапшысын.\n'
    'JSON форматында баға бер:\n'
    '{"accuracy": <1-10>, "relevance": <1-10>,\n'
    ' "no_hallucination": <1-10>, "comment": "..."}\n'
    '"""\n\n'
    'async def regression_check(groq_service, threshold=6.5) -> bool:\n'
    '    results = await run_evaluation(groq_service)\n'
    '    avg = sum(r.avg_score for r in results) / len(results)\n'
    '    return avg >= threshold  # False болса CI сәтсіздікке ұшырайды',
    caption='LLM-as-a-judge регрессия тесті (eval/judge.py):'
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  БЛОК 6
# ══════════════════════════════════════════════════════════════════════════════
heading('10. 6-БЛОК. PRODUCTION-READY ЖӘНЕ DEVOPS', 1)

task_title('28', 'Құрылымдық логтар және трассировка')
purpose(
    'Кез келген сұраныс бойынша толық тізбекті (Telegram → бот → Groq) '
    'бақылай алу мүмкіндігі.'
)
detail(
    'structlog JSON форматымен баптанды. OpenTelemetry трейстер '
    'ConsoleSpanExporter арқылы шығарылады (production-да — Jaeger). '
    'Әр сұраныс үшін бірегей request_id жасалады. '
    'Барлық жер арқылы трассировка жүреді.'
)
code(
    '# utils/logging_setup.py\n'
    'structlog.configure(\n'
    '    processors=[\n'
    '        structlog.contextvars.merge_contextvars,\n'
    '        structlog.processors.add_log_level,\n'
    '        structlog.processors.TimeStamper(fmt="iso"),\n'
    '        structlog.processors.JSONRenderer(),  # JSON форматы\n'
    '    ],\n'
    '    logger_factory=structlog.PrintLoggerFactory(),\n'
    ')',
    caption='structlog JSON логтарының баптауы:'
)

spacer()

task_title('29', 'Контейнерлеу және Docker Compose стегі')
purpose(
    '"docker compose up" бір командасымен бүкіл жобаны '
    '(бот, дерекқор, кэш, мониторинг) іске қосу.'
)
detail(
    'Dockerfile multi-stage сборкамен жасалды (builder + runtime), '
    'root емес пайдаланушы, .dockerignore. '
    'Docker Compose стегі 8 сервисті қамтиды: '
    'бот, Redis, PostgreSQL+pgvector, Ollama, '
    'Prometheus, Grafana, Jaeger, MCP HTTP сервері. '
    'Әр сервиске health check баптанды.'
)
code(
    '# docker-compose.yml (үзінді)\n'
    'services:\n'
    '  bot:\n'
    '    build: .\n'
    '    depends_on:\n'
    '      postgres: { condition: service_healthy }\n'
    '      redis:    { condition: service_healthy }\n\n'
    '  postgres:\n'
    '    image: pgvector/pgvector:pg16\n'
    '    healthcheck:\n'
    '      test: ["CMD-SHELL", "pg_isready -U postgres"]\n\n'
    '  grafana:\n'
    '    image: grafana/grafana:latest\n'
    '    ports: ["3000:3000"]\n\n'
    '# Іске қосу:\n'
    '# docker compose up -d',
    caption='Docker Compose стегі (docker-compose.yml):'
)

spacer()

task_title('30', 'GitHub Actions CI/CD пайплайны')
purpose(
    'Кодты push жасағанда автоматты тексеру, сынақтан өткізу '
    'және серверге орналастыру.'
)
detail(
    'Толық CI/CD пайплайны жасалды, кезеңдер бойынша: '
    '1) lint: ruff, mypy типтерін тексеру; '
    '2) security: bandit, safety, trivy; '
    '3) tests: 81 тест + coverage; '
    '4) eval: LLM регрессия тесті; '
    '5) build: Docker образын git-commit тегімен жинақтау; '
    '6) deploy staging: SSH арқылы автоорналастыру; '
    '7) smoke test; '
    '8) production: қолмен растаумен. '
    'Жинақтау уақыты — 8 минуттан аз.'
)
code(
    '# .github/workflows/ci.yml (үзінді)\n'
    'jobs:\n'
    '  lint:    # ruff + mypy\n'
    '  security: # bandit + safety + trivy\n'
    '  test:    # pytest + coverage\n'
    '  eval:    # LLM регрессия тесті\n'
    '  build:   # Docker образын жинақтап push ету\n'
    '  deploy-staging:    # SSH арқылы автоорналастыру\n'
    '  smoke-test:        # Staging health check\n'
    '  deploy-production: # Қолмен растаумен',
    caption='CI/CD пайплайн кезеңдері:'
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  НӘТИЖЕЛЕР
# ══════════════════════════════════════════════════════════════════════════════
heading('11. ТЕСТІЛЕУ НӘТИЖЕЛЕРІ', 1)
para(
    'Барлық автоматтандырылған тесттер сәтті аяқталды. '
    'Төмендегі кестеде тест нәтижелері келтірілген.'
)

t = doc.add_table(rows=1, cols=3)
t.style = 'Table Grid'
for i, h in enumerate(['Тест санаты', 'Саны', 'Нәтиже']):
    c = t.rows[0].cells[i]
    c.text = h
    for p2 in c.paragraphs:
        for r in p2.runs:
            r.bold = True; r.font.name = 'Times New Roman'; r.font.size = Pt(12)

test_rows = [
    ('Юниттік тесттер (handlers)',       '20', 'Өтті ✓'),
    ('Юниттік тесттер (services)',       '14', 'Өтті ✓'),
    ('Интеграциялық тесттер',            '15', 'Өтті ✓'),
    ('Қасиетке негізделген (Hypothesis)','12', 'Өтті ✓'),
    ('Қосымша тесттер',                  '20', 'Өтті ✓'),
    ('БАРЛЫҒЫ',                          '81', 'Барлығы өтті ✓'),
]
for cat, cnt, res in test_rows:
    row = t.add_row().cells
    for i, val in enumerate([cat, cnt, res]):
        row[i].text = val
        for p2 in row[i].paragraphs:
            for r in p2.runs:
                r.font.name = 'Times New Roman'; r.font.size = Pt(12)

spacer()
para('Тесттерді іске қосу командасы:', bold=True, indent=False)
code('.\\venv\\Scripts\\python.exe -m pytest tests/ -v')

spacer()
para('Кодты жабу (coverage) нәтижелері:', bold=True, indent=False)

t2 = doc.add_table(rows=1, cols=2)
t2.style = 'Table Grid'
for i, h in enumerate(['Модуль', 'Жабу']):
    c = t2.rows[0].cells[i]
    c.text = h
    for p2 in c.paragraphs:
        for r in p2.runs:
            r.bold = True; r.font.name = 'Times New Roman'; r.font.size = Pt(12)

for mod, pct in [
    ('config/settings.py',       '84%'),
    ('handlers/common.py',       '89%'),
    ('utils/tokens.py',          '88%'),
    ('services/groq_service.py', '70%'),
    ('services/rate_limiter.py', '64%'),
    ('ЖАЛПЫ',                    '53%'),
]:
    row = t2.add_row().cells
    for i, val in enumerate([mod, pct]):
        row[i].text = val
        for p2 in row[i].paragraphs:
            for r in p2.runs:
                r.font.name = 'Times New Roman'; r.font.size = Pt(12)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  ҚОРЫТЫНДЫ
# ══════════════════════════════════════════════════════════════════════════════
heading('12. ҚОРЫТЫНДЫ', 1)
para(
    'Практикалық жұмыс барысында Satbayev University студенттері үшін '
    'жасанды интеллектпен толыққанды Telegram-боты жасалды. '
    'Барлық 30 практикалық тапсырма орындалды.'
)
para(
    'Жоба заманауи Python экожүйесінің лучших практикаларын демонстрациялайды: '
    'Dependency Injection, модульдік архитектура, автоматтандырылған тестілеу, '
    'контейнерлеу және CI/CD.'
)
para('Жүзеге асырылған негізгі нәтижелер:', bold=True)

results = [
    'aiogram 3 негізіндегі модульдік архитектура, Dependency Injection паттерні',
    'Groq API интеграциясы: стриминг жауаптары, multi-model роутер, авто-суммарлау',
    'Token Bucket алгоритмі: үш деңгейлі Rate Limiter, Redis/жады fallback',
    'MCP серверлер: filesystem, PostgreSQL (RBAC), HTTP/SSE, агрегатор',
    'Ollama гибридті режим, RAG пайплайн pgvector-мен, бенчмарк',
    'Whisper дауыстық тану, LLaMA 4 Vision суреттерді талдауы',
    'Интернет іздеу Redis кэшімен, Google Calendar OAuth2, webhook',
    '81 автоматтандырылған тест: unit, integration, property-based, жүктеме',
    'LLM-as-a-judge регрессия тесті сапаны автоматты бақылау үшін',
    'structlog + OpenTelemetry, Docker Compose (8 сервис), GitHub Actions CI/CD',
]
for r in results:
    bullet(r)

spacer()
para(
    'Жасалған бот @bazikss_bot адресінде қолжетімді және нақты '
    'пайдалануға дайын. docker compose up командасымен бүкіл стекті '
    'бір командамен іске қосуға болады.',
    indent=True
)

# ─── Сақтау ──────────────────────────────────────────────────────────────────
path = r'C:\Users\User\Desktop\Esep_Telegram_Bot_KZ.docx'
doc.save(path)
print('Fayl saqtaldy:', path)
