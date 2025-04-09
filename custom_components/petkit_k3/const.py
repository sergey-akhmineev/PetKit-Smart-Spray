# const.py
DOMAIN = "petkit_k3"
PLATFORMS = ["light", "button"]

DEFAULT_REGION = "FR"
DEFAULT_TIMEZONE = "Asia/Yekaterinburg"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_REGION = "region"
CONF_TIMEZONE = "timezone"
CONF_DEVICES = "devices"

# Bluetooth-константы
CHAR_UUID = "0000aaa2-0000-1000-8000-00805f9b34fb"
INIT_CMD = "fafcfdd501000000fb"

# Команды аутентификации – вставляем секрет между префиксом и суффиксом
AUTH_CMD_PREFIX = "fafcfd56010108000000"
AUTH_CMD_SUFFIX = "fb"

# Команды для управления
SPRAY_CMD = "fafcfddc010a02000103fb"
LIGHT_CMD = "fafcfddc010b02000203fb"

SCAN_INTERVAL = 60  # период heartbeat в секундах