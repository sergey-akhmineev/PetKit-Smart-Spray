# Petkit Smart Spray Bluetooth Integration

<div align="center">
<img src="https://static.insales-cdn.com/images/products/1/6584/558168504/IMG_7256.JPG" alt="Petkit K3" width="300"/>
</div>

## 🇷🇺 Русская версия

### Функциональность:
В текущей версии поддерживаются следующие функции:
- ✨ Распыление (работает 10 секунд, затем автоматически отключается)
- 💡 Подсветка (включается на 10 секунд, не работает во время распыления)

### 🔋 Энергосбережение:
Интеграция не держит постоянное Bluetooth-соединение с K3 — именно оно быстро разряжало батарею.
- Доступность устройства определяется пассивно, по его рекламным пакетам (к устройству при этом не подключаемся).
- Соединение открывается только для отправки команды, аутентификация выполняется один раз за соединение.
- После простоя соединение закрывается (по умолчанию через 30 секунд, настраивается в *Настройки → Устройства и службы → PetKit Smart Spray → Настроить*; 0 — отключаться сразу после команды).
- Нет фонового heartbeat и автоматического переподключения. Слот подключения освобождается, что важно для ESPHome Bluetooth Proxy.

Первая команда после простоя выполняется на 1–3 секунды дольше — это время на подключение.

### Инициализация устройства:
Для работы требуется выполнить два этапа:
1. Инициализация: `fafcfdd501000000fb`
2. Аутентификация: `fafcfd560101080000001d7eaf21ed20fb`

### UUID для управления:
Основной UUID для записи команд:
- `0000aaa2-0000-1000-8000-00805f9b34fb`

### Доступные сервисы и характеристики:
```
Сервис: 00001800-0000-1000-8000-00805f9b34fb
├── Характеристика: 00002a00-0000-1000-8000-00805f9b34fb [read, notify]
├── Характеристика: 00002a01-0000-1000-8000-00805f9b34fb [read]
└── Характеристика: 00002a04-0000-1000-8000-00805f9b34fb [read]

Сервис: 00001801-0000-1000-8000-00805f9b34fb
└── Характеристика: 00002a05-0000-1000-8000-00805f9b34fb [indicate]

Сервис: 0000aaa0-0000-1000-8000-00805f9b34fb
├── Характеристика: 0000aaa2-0000-1000-8000-00805f9b34fb [write-without-response, write]
└── Характеристика: 0000aaa1-0000-1000-8000-00805f9b34fb [read, notify]
```

### 🚧 В разработке:
- Считывание уровня заряда батареи
- Мониторинг уровня жидкости
- Работа подсветки во время распыления

---

## 🇬🇧 English Version

### Functionality:
Current version supports:
- ✨ Spray function (operates for 10 seconds, then automatically turns off)
- 💡 Light function (turns on for 10 seconds, doesn't work during spraying)

### 🔋 Battery saving:
The integration no longer keeps a permanent Bluetooth connection to the K3, which was what drained the battery.
- Availability is tracked passively from the device's advertisements (no connection is made).
- A connection is opened only to send a command; authentication happens once per connection.
- The connection is closed after an idle period (30 seconds by default, configurable in *Settings → Devices & services → PetKit Smart Spray → Configure*; 0 disconnects right after each command).
- No background heartbeat and no auto-reconnect. The connection slot is released, which matters for ESPHome Bluetooth proxies.

The first command after an idle period takes 1–3 seconds longer while the connection is established.

### Device Initialization:
Two steps are required:
1. Initialization: `fafcfdd501000000fb`
2. Authentication: `fafcfd560101080000001d7eaf21ed20fb`

### Control UUID:
Main UUID for command writing:
- `0000aaa2-0000-1000-8000-00805f9b34fb`

### Available Services and Characteristics:
```
Service: 00001800-0000-1000-8000-00805f9b34fb
├── Characteristic: 00002a00-0000-1000-8000-00805f9b34fb [read, notify]
├── Characteristic: 00002a01-0000-1000-8000-00805f9b34fb [read]
└── Characteristic: 00002a04-0000-1000-8000-00805f9b34fb [read]

Service: 00001801-0000-1000-8000-00805f9b34fb
└── Characteristic: 00002a05-0000-1000-8000-00805f9b34fb [indicate]

Service: 0000aaa0-0000-1000-8000-00805f9b34fb
├── Characteristic: 0000aaa2-0000-1000-8000-00805f9b34fb [write-without-response, write]
└── Characteristic: 0000aaa1-0000-1000-8000-00805f9b34fb [read, notify]
```

### 🚧 In Development:
- Battery level reading
- Liquid level monitoring
- Operation of the backlight during spraying

Special thanks to @Jezza34000 for his library, it helped in the development of this integration.