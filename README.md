# Конкурс для Python-разработчиков от компании О2RUS
## [Описание задания](02rus_description.pdf)

### Описание проекта

+ Развертывание проекта реализован через docker-compose.yml файл.
+ Команда для запуска docker-compose up
+ Для просмотра данных в БД предусмотрено развертывание контейнера с GPAdmin4, который будет доступен по адресу http://localhost:5050/
+ Данные для подключения к GPAdmin4 (вкладка Connection): 
  + host name: postgresparserdb
  + maintenance database: pdf_parsing
  + username: postgres
  + password: 6802425
+ Данные для подключения к GPAdmin4 можно изменить в файле docker-compose.yml
+ Исходный PDF файл с именем SAE J1939-71.pdf должен находится на том же уровне, что и main.py


### Структура проекта
- Файл models.py содержит модель таблицы и необходимые переменные для подключения к БД
- Файл main.py являет основным исполняемым файлом. 
- SAE J1939-71.pdf - целевой файл, из которого извлекаются данные. Должен находится на одном уровне с main.py. Не допускается изменение имени файла, в противном случае необходимо вносить изменения в main.py
- Проект реализован с использованием Poetry. Описание зависимостей хранятся в файлах poetry.lock и pyproject.toml
- docker-compose.yml и Dockerfile - файлы, необходимые для развёртывания проекта с помощью Docker

#### Описание общей логики, реализованной в main.py
* Читаем весь файл SAE J1939-71.pdf и сохраняем тест параграфов 5.2 и 5.3 в раздельные переменные. Разделение происходит на основе номеров страниц, указанный в константах PAR_5_2_START_PAGE, PAR_5_2_END_PAGE, PAR_5_3_START_PAGE
* Подготавливаем тест из параграфов 5.2 и 5.3 для извлечения информации. Для этого разбиваем каждый текст на смысловые блоки (т.е. каждый блок это описание отдельного объекта)
* Итерируемся по каждому блоку из п.5.3, достаём значения ID, Data_length и PGN. А из таблицы для каждой записи достаём Parameter Name и Номер параграфа 5.2.
* Проваливаемся в п. 5.2. и на основании PNG, Parameter Name и Номера параграфа 5.2. ищем блок с детальным описанием.
* Из каждого блока п.5.2. извлекаем Slot Length (по условию задания это 'Length - Длина занимаемая значением'. Её значение было проще извлечь из п.5.2.), Slot Scaling, Slot Range, SPN
* Записываем данные в БД (одна запись = одна строка в таблице в п.5.3.)

