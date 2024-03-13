import re

import fitz

from models import O2Rus, session

# Константы начала и окончания параграфов 5.2 и 5.3
PAR_5_2_START_PAGE: int = 5
PAR_5_2_END_PAGE: int = 331
PAR_5_3_START_PAGE: int = 332


def _read_text_from_pages(doc, start_page, end_page=None):
    """ "Функция чтения текста из документа"""
    text: str = ""
    for page in doc.pages(start=start_page - 1, stop=end_page):
        text += page.get_text(sort=True) + chr(12)
    return text


def _split_paragraphs(text, split_pattern):
    """ "Функция разделения текста на блоки согласно паттерну"""
    return [i for i in re.split(pattern=split_pattern, string=text) if i]


def _text_preparation():
    """Функция подготовки текста.
    Результатом работы являются два списка с
    готовым для извлечения данных текстом из п.5.2 и п.5.3"""

    # Читаем файл и сохраняем тест для каждого параграфа в отдельной переменной
    with fitz.open("SAE J1939-71.pdf") as doc:
        par_5_2_text: str = _read_text_from_pages(doc, PAR_5_2_START_PAGE, PAR_5_2_END_PAGE)
        par_5_3_text: str = _read_text_from_pages(doc, PAR_5_3_START_PAGE)

    # Регулярные выражения для разделения параграфов на блоки
    par_5_2_split_pattern = re.compile(r"(?=-71\s*5\.2\.\d\.[\d|?]{2,3})" r"(.*?)(?=-71|$)")
    par_5_3_split_pattern = re.compile(r"(?=-71\s*5\.3\.[\d|?]{2,3})(.*?)" r"(?=-71|$)")

    # Списки разделенных параграфов 5.2 и 5.3
    par_5_2_result: list = _split_paragraphs(par_5_2_text, par_5_2_split_pattern)
    par_5_3_result: list = _split_paragraphs(par_5_3_text, par_5_3_split_pattern)

    # Убираем пустые строки из разделенных
    # параграфов 5.2 и 5.3 возвращаем списки
    return [i for i in par_5_2_result if i], [i for i in par_5_3_result if i]


def upload_to_db(par_5_2_result: list, par_5_3_result: list):
    """Комплексная функция по извлечения и записью данных."""

    # Паттерны для поиска данных в 5.3
    data_length_pattern = re.compile(r"(Data Length:)\s+(\w+)\s+")
    pgn_and_id_pattern = re.compile(r"(?:Parameter Group)\s+(\d{1,5})\s+" r"\(\s+(\w{1,5})\s+\)\s+")
    name_and_par_pattern = re.compile(
        r"(?:byte|bytes|bits|Variabl)\s+(.+)\s+"
        r"(?:\d{2,4})\s-71\s+(5\.2\.\d\.[\d|?]{2,3})\s+"
        r"(?:\d{1,2}\/\d{1,2}\/\d{4})?"
        r"(\s*(?:.+\))|(?:\(.+\))|(?:\s*[A-Za-z0-9]+\s))?"
    )

    # Паттерны для поиска данных в 5.2
    slot_length_pattern = re.compile(r"Slot\sLength:\s(.*?)(?=\s+Slot\sScaling)")
    slot_scaling_pattern = re.compile(r"Slot\sScaling:\s(.*?Offset)")
    slot_range_pattern = re.compile(r"Slot\sRange:\s(.*?)(?=Operational)")
    spn_pattern = re.compile(r"SPN:\s(.*?)(?=SPN)")

    with session:
        # Циклом проходимся по параграфу 5.3 и достаём целевые значения
        for state_5_3 in par_5_3_result[1:]:
            # Блок извлечения значения Data Length (может быть type str)
            data_length = re.search(data_length_pattern, state_5_3).group(2)

            # Блок извлечения значений PGN и CAN_ID
            pgn_and_id_groups = re.search(pgn_and_id_pattern, state_5_3).groups()
            pgn: str = pgn_and_id_groups[0].strip()
            can_id: str = pgn_and_id_groups[1].strip()

            # В таблице с описанием параметров может
            # содержаться различное кол-во записей.
            # Кладём все записи в переменную
            # table_with_description в список кортежей
            table_with_description = re.findall(name_and_par_pattern, state_5_3)

            # Для каждой записи в table_with_description
            # достаём наименование и номер из параграфа 5.2
            for row in table_with_description:
                paragraph_number: str = row[1].strip()
                parameter_name_5_3: str = row[0].strip()

                # Значения parameter_name неоднородны и
                # в некоторых случаях занимают 2 строчки,
                # ввиду этого выполняем ряд проверок
                # и замен для корректного формирования имени
                parameter_name_to_db: str = row[0].strip()
                if (
                    row[2]
                    and len(row[2].replace("\\n", "").strip()) > 2
                    and len(row[2]) < 30
                    and row[2].replace("\\n", "").strip() not in ["Page", "from", "The"]
                ):
                    parameter_name_to_db: str = (
                        row[0].strip() + " " + row[2].replace(" ", "").replace("\\n", "").strip()
                    )

                # Заглушка для отсутствующей в п. 5.2. записи из п.5.3, стр. 373
                if (
                    parameter_name_5_3 == "Service Component Identification"
                    and pgn == "56832"
                    and paragraph_number == "5.2.5.102"
                ):
                    continue

                # находим раздел параграфа 5.2, соответствующий строчке из
                # таблицы по pgn, названию параметра и номеру параграфа
                target_state_5_2: list = [
                    i
                    for i in par_5_2_result
                    if pgn in i and parameter_name_5_3 in i and paragraph_number in i
                ]

                # Блок извлечения значения Slot Length
                slot_length_groups = re.search(slot_length_pattern, str(target_state_5_2)).group(1)
                slot_length: str = slot_length_groups.split("\\n")[0].strip()

                # Блок извлечения значения Slot Scaling
                slot_scaling_groups = re.search(slot_scaling_pattern, str(target_state_5_2)).group(
                    1
                )
                slot_scaling: str = slot_scaling_groups.replace("\\n", "").strip()

                # Блок извлечения значения Slot Range
                slot_range_groups = re.search(slot_range_pattern, str(target_state_5_2)).group(1)
                slot_range: str = slot_range_groups.replace("\\n", "").strip()

                # Блок извлечения значения SPN
                spn_groups = re.search(spn_pattern, str(target_state_5_2)).group(1)
                spn: int = int(spn_groups.split("\\n")[1].strip())

            # Запись в БД
            data = O2Rus(
                can_id=can_id,
                data_length=data_length,
                length=slot_length,
                name=parameter_name_to_db,
                scaling=slot_scaling,
                range=slot_range,
                spn=spn,
            )
            session.add(data)
        session.commit()


if __name__ == "__main__":
    upload_to_db(*_text_preparation())
