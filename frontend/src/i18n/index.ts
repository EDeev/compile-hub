// Переводы интерфейса ru/en. Язык — useLanguageStore (у вошедшего синхронизируется с сервером).
import { create } from "zustand"
import { persist } from "zustand/middleware"

export type UiLanguage = "ru" | "en"

const ru = {
  "header.login": "Войти",
  "header.signup": "Регистрация",
  "account.settings": "Настройки",
  "account.logout": "Выйти",

  "auth.welcome": "Добро пожаловать в CompileHub!",
  "auth.login": "Войти",
  "auth.signup": "Зарегистрироваться",
  "auth.usernameOrEmail": "Имя пользователя или почта",
  "auth.username": "Имя пользователя",
  "auth.email": "Почта",
  "auth.password": "Пароль",
  "auth.confirmPassword": "Повторите пароль",
  "auth.forgot": "Забыли пароль?",
  "auth.loggedIn": "Вы вошли",
  "auth.registered": "Аккаунт создан — проверьте почту, чтобы подтвердить адрес",
  "auth.usernameFree": "Имя {name} свободно",
  "auth.usernameTaken": "Имя {name} уже занято",
  "auth.importDone": "Гостевые файлы перенесены в аккаунт: {count}",
  "auth.importSkipped": "Не поместились в лимиты: {count}",

  "validation.usernameRequired": "Введите имя пользователя",
  "validation.usernameLength": "От {min} до {max} символов",
  "validation.usernameChars": "Только латиница, цифры и подчёркивание",
  "validation.emailRequired": "Введите почту",
  "validation.emailFormat": "Неверный формат почты",
  "validation.passwordRequired": "Введите пароль",
  "validation.passwordLength": "От {min} до {max} символов",
  "validation.passwordLatin": "Только латиница, цифры и символы",
  "validation.passwordUpper": "Нужна заглавная латинская буква",
  "validation.passwordLower": "Нужна строчная латинская буква",
  "validation.passwordDigit": "Нужна цифра",
  "validation.passwordsMismatch": "Пароли не совпадают",
  "validation.fileChars": "Только латиница, цифры, _ и -",
  "validation.folderChars": "Только буквы, цифры, пробел, _ и -",
  "validation.nameLength": "Не длиннее {max} символов",
  "validation.nameEmpty": "Введите имя",
  "validation.nameTaken": "Такое имя уже есть",

  "files.search": "Поиск файлов...",
  "files.home": "Главная",
  "files.unknownFolder": "Неизвестная папка",
  "files.moveHome": "В корень",
  "files.cancel": "Отмена",
  "files.newFile": "Новый файл",
  "files.newFolder": "Новая папка",
  "files.empty": "Папка пуста",
  "files.firstHint": "Создайте первый файл или папку кнопками ниже",
  "files.notFound": "Файл «{name}» не найден",
  "files.moveHere": "Сюда",
  "files.rename": "Переименовать",
  "files.move": "Переместить",
  "files.download": "Скачать",
  "files.delete": "Удалить",
  "files.properties": "Свойства",
  "files.creating.file": "Новый файл",
  "files.creating.folder": "Новая папка",
  "files.namePlaceholder.file": "Имя файла без расширения",
  "files.namePlaceholder.folder": "Имя папки",
  "files.renaming": "Переименование: {name}",
  "files.newName": "Новое имя",
  "files.deleteTitle": "Удалить?",
  "files.deleteFile": "Файл «{name}» будет удалён безвозвратно",
  "files.deleteFolder": "Папка «{name}» будет удалена вместе со всеми файлами внутри",
  "files.propertiesOf": "Свойства: {name}",
  "files.name": "Имя",
  "files.type": "Тип",
  "files.size": "Размер",
  "files.modified": "Изменён",
  "files.language": "Язык",
  "files.guestLimit":
    "В гостевом режиме — до {folders} папок и {files} файлов. Войдите, чтобы создать больше",
  "files.guestLimitTitle": "Гостевой лимит",
  "common.ok": "OK",
  "common.cancel": "Отмена",
  "common.close": "Закрыть",
  "common.yes": "Да",
  "common.no": "Нет",
  "common.error": "Ошибка",

  "editor.greeting": "Привет, {name}",
  "editor.hint": "Откройте файл слева или создайте новый кнопкой внизу",
  "editor.hintMobile": "Откройте файл или создайте новый в списке файлов",
  "editor.openFiles": "Файлы",
  "editor.runningShort": "Выполняется — ввод в консоли",
  "editor.tab.code": "Код",
  "editor.tab.input": "Ввод",
  "editor.tab.console": "Консоль",
  "editor.run": "Запустить",
  "editor.stop": "Стоп",
  "editor.save": "Сохранить",
  "editor.saved": "Сохранено",
  "editor.unsaved": "Есть несохранённые изменения",
  "editor.stdin": "Входные данные",
  "editor.stdinPlaceholder": "Если пусто — программа читает ввод прямо из консоли",
  "editor.clear": "Очистить",
  "editor.queued": "В очереди: {position}",
  "editor.compiling": "Компиляция…",
  "editor.running":
    "Выполняется — можно вводить данные в консоли (Ctrl+D — конец ввода, Ctrl+C — остановить)",
  "editor.languageDisabled": "{language} пока недоступен для запуска",
  "editor.exitCode": "код {code}",
  "editor.signal": "сигнал {signal}",

  "verdict.OK": "Готово",
  "verdict.COMPILE_ERROR": "Ошибка компиляции",
  "verdict.RUNTIME_ERROR": "Ошибка выполнения",
  "verdict.TIME_LIMIT": "Превышено время",
  "verdict.MEMORY_LIMIT": "Превышена память",
  "verdict.OUTPUT_LIMIT": "Слишком большой вывод",
  "verdict.CANCELLED": "Остановлено",
  "verdict.INTERNAL_ERROR": "Внутренняя ошибка сервера",

  "settings.general": "Общие",
  "settings.editor": "Редактор",
  "settings.about": "О проекте",
  "settings.generalTitle": "Общие настройки",
  "settings.language": "Язык интерфейса",
  "settings.theme": "Тема",
  "settings.logout": "Выход из аккаунта",
  "settings.emailNotVerified": "Почта не подтверждена",
  "settings.emailVerified": "Почта подтверждена",
  "settings.resend": "Отправить письмо ещё раз",
  "settings.resent": "Письмо отправлено",
  "settings.usage":
    "Файлы: {files} из {maxFiles} · Папки: {folders} из {maxFolders} · Запусков сегодня: {runs}",
  "settings.unlimited": "∞",
  "settings.editorTitle": "Настройки редактора",
  "settings.fontSize": "Размер шрифта",
  "settings.snippets": "Подсказки",
  "settings.aboutTitle": "О CompileHub",
  "settings.aboutText":
    "CompileHub — онлайн-компилятор: пишите код в браузере, запускайте его в изолированной песочнице и вводите данные прямо в консоли.",
  "settings.languages": "Языки",
  "settings.authors": "Авторы",
  "settings.design": "дизайн и исходный фронтенд",
  "settings.backend": "бэкенд, песочница, фронтенд",
  "settings.changePassword": "Сменить пароль",
  "settings.currentPassword": "Текущий пароль",
  "settings.newPassword": "Новый пароль",
  "settings.passwordChanged": "Пароль изменён",

  "oauth.or": "или",
  "oauth.loginWith": "Войти через {name}",
  "oauth.title": "Вход через сервисы",
  "oauth.link": "Привязать",
  "oauth.unlink": "Отвязать",
  "oauth.linked": "Аккаунт сервиса привязан",
  "oauth.error.invalid_state":
    "Вход прерван: ссылка устарела или открыта в другом браузере — попробуйте ещё раз",
  "oauth.error.cancelled": "Вход через сервис отменён",
  "oauth.error.provider_error": "Сервис не ответил — попробуйте ещё раз",
  "oauth.error.no_email":
    "Сервис не передал почту — разрешите доступ к почте или зарегистрируйтесь обычным способом",
  "oauth.error.already_linked": "Этот аккаунт сервиса уже привязан к другому пользователю",
  "settings.setPassword": "Задать пароль",
  "error.last_login_method": "Сначала задайте пароль — иначе войти будет нечем",
  "verify.title": "Подтверждение почты",
  "verify.progress": "Проверяем ссылку…",
  "verify.ok": "Почта подтверждена — спасибо!",
  "verify.toMain": "Перейти к редактору",

  "reset.title": "Восстановление доступа",
  "reset.emailPlaceholder": "Почта аккаунта",
  "reset.send": "Отправить ссылку",
  "reset.sent":
    "Если почта {email} зарегистрирована и подтверждена, на неё отправлена ссылка для сброса пароля",
  "reset.newTitle": "Новый пароль",
  "reset.save": "Сохранить пароль",
  "reset.done": "Пароль изменён — теперь можно войти",

  "notFound.title": "Страница не найдена",
  "notFound.back": "На главную",

  "error.network_error": "Нет связи с сервером",
  "error.invalid_credentials": "Неверный логин или пароль",
  "error.username_taken": "Имя пользователя уже занято",
  "error.email_taken": "На эту почту уже есть аккаунт",
  "error.name_taken": "Такое имя уже есть",
  "error.rate_limited": "Слишком много запросов — попробуйте через {retryAfter} с",
  "error.file_limit_reached": "Достигнут лимит файлов ({limit})",
  "error.folder_limit_reached": "Достигнут лимит папок ({limit})",
  "error.code_too_large": "Код слишком большой ({limit} байт максимум)",
  "error.daily_quota_exceeded": "Исчерпан дневной лимит запусков ({limit})",
  "error.queue_full": "Сейчас слишком много запусков — попробуйте через несколько секунд",
  "error.overheated": "Сервер остывает — попробуйте через минуту",
  "error.no_workers": "Запуск кода временно недоступен",
  "error.language_disabled": "Этот язык пока недоступен для запуска",
  "error.unknown_language": "Неизвестный язык",
  "error.invalid_token": "Ссылка недействительна или устарела",
  "error.wrong_password": "Неверный пароль",
  "error.already_verified": "Почта уже подтверждена",
  "error.validation_error": "Проверьте введённые данные",
  "error.not_found": "Не найдено",
  "error.unauthorized": "Нужно войти",
  "error.default": "Что-то пошло не так, попробуйте ещё раз"
} as const

export type MessageKey = keyof typeof ru

const en: Record<MessageKey, string> = {
  "header.login": "Log In",
  "header.signup": "Sign Up",
  "account.settings": "Settings",
  "account.logout": "Log Out",

  "auth.welcome": "Welcome to CompileHub!",
  "auth.login": "Log In",
  "auth.signup": "Sign Up",
  "auth.usernameOrEmail": "Username or email",
  "auth.username": "Username",
  "auth.email": "Email",
  "auth.password": "Password",
  "auth.confirmPassword": "Confirm password",
  "auth.forgot": "Forgot password?",
  "auth.loggedIn": "You're logged in",
  "auth.registered": "Account created — check your email to confirm the address",
  "auth.usernameFree": "Username {name} is available",
  "auth.usernameTaken": "Username {name} is already taken",
  "auth.importDone": "Guest files moved to your account: {count}",
  "auth.importSkipped": "Didn't fit into limits: {count}",

  "validation.usernameRequired": "Username is required",
  "validation.usernameLength": "{min} to {max} characters",
  "validation.usernameChars": "Latin letters, digits and underscores only",
  "validation.emailRequired": "Email is required",
  "validation.emailFormat": "Invalid email format",
  "validation.passwordRequired": "Password is required",
  "validation.passwordLength": "{min} to {max} characters",
  "validation.passwordLatin": "Latin letters, digits and symbols only",
  "validation.passwordUpper": "Needs an uppercase latin letter",
  "validation.passwordLower": "Needs a lowercase latin letter",
  "validation.passwordDigit": "Needs a digit",
  "validation.passwordsMismatch": "Passwords don't match",
  "validation.fileChars": "Latin letters, digits, _ and - only",
  "validation.folderChars": "Letters, digits, spaces, _ and - only",
  "validation.nameLength": "At most {max} characters",
  "validation.nameEmpty": "Enter a name",
  "validation.nameTaken": "This name is already taken",

  "files.search": "Search files...",
  "files.home": "Home",
  "files.unknownFolder": "Unknown folder",
  "files.moveHome": "Move to home",
  "files.cancel": "Cancel",
  "files.newFile": "New file",
  "files.newFolder": "New folder",
  "files.empty": "This folder is empty",
  "files.firstHint": "Use the buttons below to create your first file or folder",
  "files.notFound": 'File "{name}" not found',
  "files.moveHere": "Move here",
  "files.rename": "Rename",
  "files.move": "Move",
  "files.download": "Download",
  "files.delete": "Delete",
  "files.properties": "Properties",
  "files.creating.file": "New file",
  "files.creating.folder": "New folder",
  "files.namePlaceholder.file": "File name without extension",
  "files.namePlaceholder.folder": "Folder name",
  "files.renaming": "Renaming {name}",
  "files.newName": "New name",
  "files.deleteTitle": "Delete?",
  "files.deleteFile": 'File "{name}" will be deleted permanently',
  "files.deleteFolder": 'Folder "{name}" will be deleted with all files inside',
  "files.propertiesOf": "Properties of {name}",
  "files.name": "Name",
  "files.type": "Type",
  "files.size": "Size",
  "files.modified": "Modified",
  "files.language": "Language",
  "files.guestLimit":
    "Guest mode allows up to {folders} folders and {files} files. Log in to create more",
  "files.guestLimitTitle": "Guest limit",
  "common.ok": "OK",
  "common.cancel": "Cancel",
  "common.close": "Close",
  "common.yes": "Yes",
  "common.no": "No",
  "common.error": "Error",

  "editor.greeting": "Hi, {name}",
  "editor.hint": "Open a file on the left or create a new one with the button at the bottom",
  "editor.hintMobile": "Open a file or create a new one in the file list",
  "editor.openFiles": "Files",
  "editor.runningShort": "Running — type input in the console",
  "editor.tab.code": "Code",
  "editor.tab.input": "Input",
  "editor.tab.console": "Console",
  "editor.run": "Run",
  "editor.stop": "Stop",
  "editor.save": "Save",
  "editor.saved": "Saved",
  "editor.unsaved": "Unsaved changes",
  "editor.stdin": "Input",
  "editor.stdinPlaceholder": "Leave empty to type input right in the console",
  "editor.clear": "Clear",
  "editor.queued": "Queued: {position}",
  "editor.compiling": "Compiling…",
  "editor.running": "Running — you can type input in the console (Ctrl+D ends input, Ctrl+C stops)",
  "editor.languageDisabled": "{language} can't be run yet",
  "editor.exitCode": "exit code {code}",
  "editor.signal": "signal {signal}",

  "verdict.OK": "Done",
  "verdict.COMPILE_ERROR": "Compilation error",
  "verdict.RUNTIME_ERROR": "Runtime error",
  "verdict.TIME_LIMIT": "Time limit exceeded",
  "verdict.MEMORY_LIMIT": "Memory limit exceeded",
  "verdict.OUTPUT_LIMIT": "Output too large",
  "verdict.CANCELLED": "Stopped",
  "verdict.INTERNAL_ERROR": "Internal server error",

  "settings.general": "General",
  "settings.editor": "Editor",
  "settings.about": "About",
  "settings.generalTitle": "General settings",
  "settings.language": "Interface language",
  "settings.theme": "Theme",
  "settings.logout": "Log out",
  "settings.emailNotVerified": "Email not confirmed",
  "settings.emailVerified": "Email confirmed",
  "settings.resend": "Resend the email",
  "settings.resent": "Email sent",
  "settings.usage":
    "Files: {files} of {maxFiles} · Folders: {folders} of {maxFolders} · Runs today: {runs}",
  "settings.unlimited": "∞",
  "settings.editorTitle": "Editor settings",
  "settings.fontSize": "Font size",
  "settings.snippets": "Suggestions",
  "settings.aboutTitle": "About CompileHub",
  "settings.aboutText":
    "CompileHub is an online compiler: write code in the browser, run it in an isolated sandbox and type input right in the console.",
  "settings.languages": "Languages",
  "settings.authors": "Authors",
  "settings.design": "design and original frontend",
  "settings.backend": "backend, sandbox, frontend",
  "settings.changePassword": "Change password",
  "settings.currentPassword": "Current password",
  "settings.newPassword": "New password",
  "settings.passwordChanged": "Password changed",

  "oauth.or": "or",
  "oauth.loginWith": "Continue with {name}",
  "oauth.title": "Sign-in services",
  "oauth.link": "Link",
  "oauth.unlink": "Unlink",
  "oauth.linked": "Account linked",
  "oauth.error.invalid_state":
    "Sign-in interrupted: the link expired or was opened in another browser — try again",
  "oauth.error.cancelled": "Sign-in was cancelled",
  "oauth.error.provider_error": "The service didn't respond — try again",
  "oauth.error.no_email":
    "The service didn't share your email — allow email access or sign up the usual way",
  "oauth.error.already_linked": "This service account is already linked to another user",
  "settings.setPassword": "Set password",
  "error.last_login_method": "Set a password first — otherwise you won't be able to log in",
  "verify.title": "Email confirmation",
  "verify.progress": "Checking the link…",
  "verify.ok": "Email confirmed — thank you!",
  "verify.toMain": "Go to the editor",

  "reset.title": "Recovering access",
  "reset.emailPlaceholder": "Account email",
  "reset.send": "Send reset link",
  "reset.sent": "If {email} is registered and confirmed, a password reset link has been sent to it",
  "reset.newTitle": "New password",
  "reset.save": "Save password",
  "reset.done": "Password changed — you can log in now",

  "notFound.title": "Page not found",
  "notFound.back": "Back to main page",

  "error.network_error": "No connection to the server",
  "error.invalid_credentials": "Wrong login or password",
  "error.username_taken": "Username is already taken",
  "error.email_taken": "An account with this email already exists",
  "error.name_taken": "This name is already taken",
  "error.rate_limited": "Too many requests — try again in {retryAfter} s",
  "error.file_limit_reached": "File limit reached ({limit})",
  "error.folder_limit_reached": "Folder limit reached ({limit})",
  "error.code_too_large": "Code is too large ({limit} bytes max)",
  "error.daily_quota_exceeded": "Daily run limit reached ({limit})",
  "error.queue_full": "Too many runs right now — try again in a few seconds",
  "error.overheated": "The server is cooling down — try again in a minute",
  "error.no_workers": "Code execution is temporarily unavailable",
  "error.language_disabled": "This language can't be run yet",
  "error.unknown_language": "Unknown language",
  "error.invalid_token": "The link is invalid or expired",
  "error.wrong_password": "Wrong password",
  "error.already_verified": "Email is already confirmed",
  "error.validation_error": "Check the entered data",
  "error.not_found": "Not found",
  "error.unauthorized": "Please log in",
  "error.default": "Something went wrong, please try again"
}

const dictionaries: Record<UiLanguage, Record<MessageKey, string>> = { ru, en }

interface LanguageState {
  language: UiLanguage
  setLanguage: (language: UiLanguage) => void
}

const initialLanguage = (): UiLanguage =>
  typeof navigator !== "undefined" && navigator.language?.startsWith("ru") === false ? "en" : "ru"

export const useLanguageStore = create<LanguageState>()(
  persist(
    (set) => ({
      language: initialLanguage(),
      setLanguage: (language) => {
        document.documentElement.lang = language
        set({ language })
      }
    }),
    { name: "ui-language" }
  )
)

type Params = Record<string, string | number | null | undefined>

export const translate = (language: UiLanguage, key: MessageKey, params: Params = {}): string =>
  dictionaries[language][key].replace(/\{(\w+)\}/g, (_, name: string) => String(params[name] ?? ""))

/** t() вне React — по текущему языку стора. */
export const t = (key: MessageKey, params?: Params) =>
  translate(useLanguageStore.getState().language, key, params)

/** Хук: компонент перерисовывается при смене языка. */
export const useT = () => {
  const language = useLanguageStore((s) => s.language)
  return (key: MessageKey, params?: Params) => translate(language, key, params)
}

/** Сообщение об ошибке API по её коду. */
export const errorMessage = (error: unknown): string => {
  const e = error as { code?: string; details?: Params; message?: string }
  const key = `error.${e?.code}` as MessageKey
  if (e?.code && key in ru) return t(key, e.details ?? {})
  return t("error.default")
}
