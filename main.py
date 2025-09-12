import mysql.connector
from mysql.connector import Error
import csv
import sys
import os


class UniversityDB:
    def __init__(self):
        self.connection = None

    def connect_to_db(self, host, user, password):
        """Установка соединения с базой данных"""
        try:
            # Сначала пробуем подключиться без указания базы данных
            temp_conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password
            )

            # Создаем базу данных если ее нет
            cursor = temp_conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS study")
            print("✅ База данных 'study' создана или уже существует")
            cursor.close()
            temp_conn.close()

            # Теперь подключаемся к конкретной базе данных
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database='study'
            )

            if self.connection.is_connected():
                print("✅ Успешное подключение к базе данных study")
                return True

        except Error as e:
            print(f"❌ Ошибка подключения к MySQL: {e}")
            return False

    def create_tables(self):
        """Создание таблиц students и disciplines"""
        try:
            cursor = self.connection.cursor()

            # Создание таблицы students
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    course_number INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Создание таблицы disciplines
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS disciplines (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    discipline_name VARCHAR(100) NOT NULL,
                    day_of_week VARCHAR(20) NOT NULL,
                    lesson_number INT NOT NULL,
                    course_number INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.connection.commit()
            print("✅ Таблицы 'students' и 'disciplines' созданы успешно")
            cursor.close()
            return True

        except Error as e:
            print(f"❌ Ошибка при создании таблиц: {e}")
            return False

    def import_students_from_csv(self, csv_file_path='students.csv'):
        """Импорт данных о студентах из CSV файла"""
        try:
            if not os.path.exists(csv_file_path):
                print(f"⚠️ Файл {csv_file_path} не найден")
                print("Создайте файл students.csv с данными в формате:")
                print("ID[TAB]Name[TAB]Course")
                print("1[TAB]Bennie Hodkiewicz[TAB]1")
                return False

            cursor = self.connection.cursor()

            # Очистка таблицы перед импортом
            cursor.execute("DELETE FROM students")

            imported_count = 0
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                # Пробуем разные разделители
                for delimiter in ['\t', ',', ';']:
                    file.seek(0)
                    try:
                        csv_reader = csv.reader(file, delimiter=delimiter)
                        for row_num, row in enumerate(csv_reader, 1):
                            if len(row) >= 3:
                                try:
                                    student_id = int(row[0].strip())
                                    name = row[1].strip()
                                    course_number = int(row[2].strip())

                                    cursor.execute(
                                        "INSERT INTO students (id, name, course_number) VALUES (%s, %s, %s)",
                                        (student_id, name, course_number)
                                    )
                                    imported_count += 1

                                except (ValueError, Error):
                                    continue
                        break
                    except:
                        continue

            self.connection.commit()
            print(f"✅ Импортировано {imported_count} студентов")
            cursor.close()
            return True

        except Error as e:
            print(f"❌ Ошибка при импорте данных: {e}")
            return False

    def get_student(self, student_id):
        """Получение студента по ID"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM students WHERE id = %s",
                (student_id,)
            )
            student = cursor.fetchone()
            cursor.close()
            return student
        except Error as e:
            print(f"❌ Ошибка при получении студента: {e}")
            return None

    def get_disciplines_by_course(self, course_number):
        """Получение всех занятий по номеру курса"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM disciplines WHERE course_number = %s ORDER BY day_of_week, lesson_number",
                (course_number,)
            )
            disciplines = cursor.fetchall()
            cursor.close()
            return disciplines
        except Error as e:
            print(f"❌ Ошибка при получении дисциплин: {e}")
            return []

    def get_students_by_course(self, course_number):
        """Получение всех студентов по номеру курса"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM students WHERE course_number = %s ORDER BY name",
                (course_number,)
            )
            students = cursor.fetchall()
            cursor.close()
            return students
        except Error as e:
            print(f"❌ Ошибка при получении студентов: {e}")
            return []

    def get_all_disciplines(self):
        """Получение полного расписания"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM disciplines ORDER BY course_number, day_of_week, lesson_number"
            )
            disciplines = cursor.fetchall()
            cursor.close()
            return disciplines
        except Error as e:
            print(f"❌ Ошибка при получении расписания: {e}")
            return []

    def add_student(self, name, course_number):
        """Добавление нового студента"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT MAX(id) as max_id FROM students")
            result = cursor.fetchone()
            new_id = (result[0] or 0) + 1

            cursor.execute(
                "INSERT INTO students (id, name, course_number) VALUES (%s, %s, %s)",
                (new_id, name, int(course_number))
            )
            self.connection.commit()
            print(f"✅ Студент '{name}' добавлен (ID: {new_id})")
            cursor.close()
            return True
        except Error as e:
            print(f"❌ Ошибка при добавлении студента: {e}")
            return False

    def add_discipline(self, discipline_name, day_of_week, lesson_number, course_number):
        """Добавление нового занятия"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO disciplines (discipline_name, day_of_week, lesson_number, course_number) VALUES (%s, %s, %s, %s)",
                (discipline_name, day_of_week, int(lesson_number), int(course_number))
            )
            self.connection.commit()
            discipline_id = cursor.lastrowid
            print(f"✅ Дисциплина '{discipline_name}' добавлена (ID: {discipline_id})")
            cursor.close()
            return True
        except Error as e:
            print(f"❌ Ошибка при добавлении дисциплины: {e}")
            return False

    def delete_student(self, student_id):
        """Удаление студента по ID"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
            self.connection.commit()
            if cursor.rowcount > 0:
                print(f"✅ Студент с ID {student_id} удален")
            else:
                print(f"⚠️ Студент с ID {student_id} не найден")
            cursor.close()
            return True
        except Error as e:
            print(f"❌ Ошибка при удалении студента: {e}")
            return False

    def delete_discipline(self, discipline_id):
        """Удаление занятия по ID"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM disciplines WHERE id = %s", (discipline_id,))
            self.connection.commit()
            if cursor.rowcount > 0:
                print(f"✅ Занятие с ID {discipline_id} удалено")
            else:
                print(f"⚠️ Занятие с ID {discipline_id} не найдено")
            cursor.close()
            return True
        except Error as e:
            print(f"❌ Ошибка при удалении занятия: {e}")
            return False

    def close_connection(self):
        """Закрытие соединения с базой данных"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔌 Соединение закрыто")


def get_mysql_credentials():
    """Получение данных для подключения к MySQL"""
    print("🔧 Настройка подключения к MySQL")
    print("=" * 40)

    host = input("Хост (по умолчанию localhost): ").strip() or 'localhost'
    user = input("Пользователь (по умолчанию root): ").strip() or 'root'
    password = input("Пароль (если есть): ").strip()

    return host, user, password


def test_mysql_connection(host, user, password):
    """Тестирование подключения к MySQL"""
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        if conn.is_connected():
            print("✅ Подключение к MySQL успешно!")
            conn.close()
            return True
    except Error as e:
        print(f"❌ Ошибка подключения: {e}")
        return False


def create_sample_csv():
    """Создание примера CSV файла"""
    sample_data = """1	Bennie Hodkiewicz	1
2	Octavia Huels	2
3	Elta Okuneva	3
4	Mr. Destin Murazik	4
5	Shaniya Hane	5
6	Abbie Ratke	6
7	Mrs. Michelle Lubowitz	7
8	Kassandra Emmerich PhD	8
9	Mallie Kautzer	1"""

    with open('students.csv', 'w', encoding='utf-8') as f:
        f.write(sample_data)
    print("✅ Пример файла students.csv создан")


def main():
    """Основная функция"""
    print("🎓 Университетская база данных")
    print("=" * 40)

    # Получаем данные для подключения
    host, user, password = get_mysql_credentials()

    # Тестируем подключение
    if not test_mysql_connection(host, user, password):
        print("\n❌ Не удалось подключиться к MySQL")
        print("Проверьте:")
        print("1. Запущен ли MySQL сервер")
        print("2. Правильность логина и пароля")
        return

    # Создаем и подключаем базу данных
    db = UniversityDB()
    if not db.connect_to_db(host, user, password):
        return

    # Создаем таблицы
    if not db.create_tables():
        return

    # Создаем пример CSV файла если его нет
    if not os.path.exists('students.csv'):
        create_sample_csv()

    # Импортируем данные
    db.import_students_from_csv()

    print("\n" + "=" * 60)
    print("Доступные команды:")
    print("GET student <id>          - студент по ID")
    print("GET discipline <курс>     - занятия по курсу")
    print("GET students <курс>       - студенты по курсу")
    print("GET disciplines           - все занятия")
    print("PUT student <имя> <курс>  - добавить студента")
    print("PUT discipline <название> <день> <пара> <курс> - добавить занятие")
    print("DELETE student <id>       - удалить студента")
    print("DELETE discipline <id>    - удалить занятие")
    print("exit                      - выход")
    print("=" * 60)

    while True:
        try:
            command = input("\n> ").strip()

            if command.lower() == 'exit':
                break

            parts = command.split()
            if len(parts) < 2:
                print("❌ Неверный формат")
                continue

            action = parts[0].upper()

            if action == 'GET':
                if parts[1].lower() == 'student' and len(parts) == 3:
                    student = db.get_student(parts[2])
                    if student:
                        print(f"🎓 ID: {student['id']}, Имя: {student['name']}, Курс: {student['course_number']}")
                    else:
                        print("❌ Студент не найден")

                elif parts[1].lower() == 'discipline' and len(parts) == 3:
                    disciplines = db.get_disciplines_by_course(parts[2])
                    for disc in disciplines:
                        print(f"📚 {disc['discipline_name']} ({disc['day_of_week']}, пара {disc['lesson_number']})")

                elif parts[1].lower() == 'students' and len(parts) == 3:
                    students = db.get_students_by_course(parts[2])
                    for student in students:
                        print(f"🎓 {student['name']} (ID: {student['id']})")

                elif parts[1].lower() == 'disciplines' and len(parts) == 2:
                    disciplines = db.get_all_disciplines()
                    for disc in disciplines:
                        print(
                            f"📚 {disc['discipline_name']} - {disc['day_of_week']} пара {disc['lesson_number']} (курс {disc['course_number']})")

            elif action == 'PUT':
                if parts[1].lower() == 'student' and len(parts) >= 4:
                    name = ' '.join(parts[2:-1])
                    course = parts[-1]
                    db.add_student(name, course)

                elif parts[1].lower() == 'discipline' and len(parts) >= 6:
                    discipline_name = ' '.join(parts[2:-3])
                    day = parts[-3]
                    lesson = parts[-2]
                    course = parts[-1]
                    db.add_discipline(discipline_name, day, lesson, course)

            elif action == 'DELETE':
                if parts[1].lower() == 'student' and len(parts) == 3:
                    db.delete_student(parts[2])

                elif parts[1].lower() == 'discipline' and len(parts) == 3:
                    db.delete_discipline(parts[2])

            else:
                print("❌ Неизвестная команда")

        except KeyboardInterrupt:
            print("\n👋 Выход...")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")

    db.close_connection()


if __name__ == "__main__":
    main()