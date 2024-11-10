# Petkit Smart Spray Bluetooth Integration

<div align="center">
<img src="https://static.insales-cdn.com/images/products/1/6584/558168504/IMG_7256.JPG" alt="Petkit K3" width="300"/>
</div>

## 🇷🇺 Русская версия

### Функциональность:
В текущей версии поддерживаются следующие функции:
- ✨ Распыление (работает 10 секунд, затем автоматически отключается)
- 💡 Подсветка (включается на 10 секунд, не работает во время распыления)

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