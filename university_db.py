import mysql.connector
from mysql.connector import Error
import csv
import sys
import os


class UniversityDB:
    def __init__(self):
        self.connection = None
        self.connect_to_db()

    def connect_to_db(self):
        """Установка соединения с базой данных"""
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                user='root',  # измените если нужно
                password='',  # измените если нужно
                database='study'
            )
            if self.connection.is_connected():
                print("✅ Успешное подключение к базе данных study")
        except Error as e:
            print(f"❌ Ошибка подключения к MySQL: {e}")
            print("Проверьте:\n1. Запущен ли MySQL сервер\n2. Правильность логина/пароля")
            sys.exit(1)

    def create_database(self):
        """Создание базы данных study"""
        try:
            # Временное подключение для создания БД
            temp_conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password=''
            )
            cursor = temp_conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS study")
            print("✅ База данных 'study' создана или уже существует")
            cursor.close()
            temp_conn.close()
        except Error as e:
            print(f"❌ Ошибка при создании базы данных: {e}")

    def create_tables(self):
        """Создание таблиц students и disciplines"""
        try:
            cursor = self.connection.cursor()

            # Создание таблицы students
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    course_number INT NOT NULL CHECK (course_number BETWEEN 1 AND 8),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Создание таблицы disciplines
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS disciplines (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    discipline_name VARCHAR(100) NOT NULL,
                    day_of_week ENUM('Понедельник', 'Вторник', 'Среда', 
                                   'Четверг', 'Пятница', 'Суббота') NOT NULL,
                    lesson_number INT NOT NULL CHECK (lesson_number BETWEEN 1 AND 8),
                    course_number INT NOT NULL CHECK (course_number BETWEEN 1 AND 8),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.connection.commit()
            print("✅ Таблицы 'students' и 'disciplines' созданы успешно")
            cursor.close()

        except Error as e:
            print(f"❌ Ошибка при создании таблиц: {e}")

    def import_students_from_csv(self, csv_file_path='students.csv'):
        """Импорт данных о студентах из CSV файла с табуляцией как разделителем"""
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
                # Используем табуляцию как разделитель
                csv_reader = csv.reader(file, delimiter='\t')

                for row_num, row in enumerate(csv_reader, 1):
                    if len(row) >= 3:
                        try:
                            student_id = int(row[0].strip())
                            name = row[1].strip()
                            course_number = int(row[2].strip())

                            # Проверяем корректность номера курса
                            if not (1 <= course_number <= 8):
                                print(f"⚠️ Строка {row_num}: некорректный номер курса '{course_number}'")
                                continue

                            cursor.execute(
                                "INSERT INTO students (id, name, course_number) VALUES (%s, %s, %s)",
                                (student_id, name, course_number)
                            )
                            imported_count += 1

                        except ValueError as e:
                            print(f"⚠️ Строка {row_num}: ошибка преобразования данных - {e}")
                            continue
                        except Error as e:
                            if "Duplicate entry" in str(e):
                                print(f"⚠️ Строка {row_num}: студент с ID {student_id} уже существует")
                            else:
                                print(f"⚠️ Строка {row_num}: ошибка БД - {e}")
                            continue
                    else:
                        print(f"⚠️ Строка {row_num}: неполные данные - {row}")

            self.connection.commit()
            print(f"✅ Импортировано {imported_count} студентов из файла {csv_file_path}")
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
        """Получение всех занятий по номеру курса в хронологическом порядке"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            cursor.execute(
                """SELECT * FROM disciplines 
                   WHERE course_number = %s 
                   ORDER BY 
                     FIELD(day_of_week, 'Понедельник', 'Вторник', 'Среда', 
                           'Четверг', 'Пятница', 'Суббота'), 
                     lesson_number""",
                (course_number,)
            )

            disciplines = cursor.fetchall()
            cursor.close()
            return disciplines
        except Error as e:
            print(f"❌ Ошибка при получении дисциплин: {e}")
            return []

    def get_students_by_course(self, course_number):
        """Получение всех студентов по номеру курса в алфавитном порядке"""
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
                """SELECT * FROM disciplines 
                   ORDER BY course_number, 
                     FIELD(day_of_week, 'Понедельник', 'Вторник', 'Среда', 
                           'Четверг', 'Пятница', 'Суббота'), 
                     lesson_number"""
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

            # Получаем максимальный ID для нового студента
            cursor.execute("SELECT MAX(id) as max_id FROM students")
            result = cursor.fetchone()
            new_id = (result[0] or 0) + 1

            cursor.execute(
                "INSERT INTO students (id, name, course_number) VALUES (%s, %s, %s)",
                (new_id, name, int(course_number))
            )
            self.connection.commit()
            print(f"✅ Студент '{name}' успешно добавлен на курс {course_number} (ID: {new_id})")
            cursor.close()
            return True
        except Error as e:
            print(f"❌ Ошибка при добавлении студента: {e}")
            return False

    def add_discipline(self, discipline_name, day_of_week, lesson_number, course_number):
        """Добавление нового занятия"""
        try:
            # Проверяем корректность дня недели
            valid_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
            if day_of_week not in valid_days:
                print(f"❌ Ошибка: день недели должен быть одним из: {', '.join(valid_days)}")
                return False

            cursor = self.connection.cursor()
            cursor.execute(
                """INSERT INTO disciplines 
                   (discipline_name, day_of_week, lesson_number, course_number) 
                   VALUES (%s, %s, %s, %s)""",
                (discipline_name, day_of_week, int(lesson_number), int(course_number))
            )
            self.connection.commit()
            discipline_id = cursor.lastrowid
            print(f"✅ Дисциплина '{discipline_name}' успешно добавлена (ID: {discipline_id})")
            cursor.close()
            return True
        except Error as e:
            print(f"❌ Ошибка при добавлении дисциплины: {e}")
            return False

    def delete_student(self, student_id):
        """Удаление студента по ID"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "DELETE FROM students WHERE id = %s",
                (student_id,)
            )
            self.connection.commit()
            if cursor.rowcount > 0:
                print(f"✅ Студент с ID {student_id} успешно удален")
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
            cursor.execute(
                "DELETE FROM disciplines WHERE id = %s",
                (discipline_id,)
            )
            self.connection.commit()
            if cursor.rowcount > 0:
                print(f"✅ Занятие с ID {discipline_id} успешно удалено")
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
            print("🔌 Соединение с базой данных закрыто")


def print_student(student):
    """Вывод информации о студенте"""
    if student:
        print("=" * 50)
        print(f"🎓 СТУДЕНТ")
        print("=" * 50)
        print(f"ID: {student['id']}")
        print(f"Имя: {student['name']}")
        print(f"Курс: {student['course_number']}")
        print(f"Дата создания: {student['created_at']}")
        print("=" * 50)
    else:
        print("❌ Студент не найден")


def print_disciplines(disciplines):
    """Вывод информации о дисциплинах"""
    if disciplines:
        print(f"\n📚 Найдено дисциплин: {len(disciplines)}")
        print("=" * 60)
        for disc in disciplines:
            print(f"ID: {disc['id']}")
            print(f"Дисциплина: {disc['discipline_name']}")
            print(f"День: {disc['day_of_week']}")
            print(f"Пара: {disc['lesson_number']}")
            print(f"Курс: {disc['course_number']}")
            print(f"Дата создания: {disc['created_at']}")
            print("-" * 40)
    else:
        print("❌ Дисциплины не найдены")


def print_students(students):
    """Вывод информации о студентах"""
    if students:
        print(f"\n🎓 Найдено студентов: {len(students)}")
        print("=" * 50)
        for student in students:
            print(f"ID: {student['id']}")
            print(f"Имя: {student['name']}")
            print(f"Курс: {student['course_number']}")
            print(f"Дата создания: {student['created_at']}")
            print("-" * 30)
    else:
        print("❌ Студенты не найдены")


def main():
    """Основная функция с консольным интерфейсом"""
    db = UniversityDB()

    # Создание базы данных и таблиц при первом запуске
    db.create_database()
    db.connect_to_db()
    db.create_tables()

    # Импорт данных из CSV
    db.import_students_from_csv('students.csv')

    print("\n" + "=" * 70)
    print("🎓 УНИВЕРСИТЕТСКАЯ БАЗА ДАННЫХ - КОНСОЛЬНЫЙ ИНТЕРФЕЙС")
    print("=" * 70)
    print("Доступные команды:")
    print("GET student <id>          - получить студента по ID")
    print("GET discipline <курс>     - получить занятия по курсу")
    print("GET students <курс>       - получить студентов по курсу")
    print("GET disciplines           - получить все занятия")
    print("PUT student <имя> <курс>  - добавить студента")
    print("PUT discipline <название> <день> <пара> <курс> - добавить занятие")
    print("DELETE student <id>       - удалить студента")
    print("DELETE discipline <id>    - удалить занятие")
    print("exit                      - выход из программы")
    print("=" * 70)

    while True:
        try:
            command = input("\n🎯 Введите команду: ").strip()

            if command.lower() == 'exit':
                break

            parts = command.split()
            if len(parts) < 2:
                print("❌ Неверный формат команды")
                continue

            action = parts[0].upper()

            if action == 'GET':
                if parts[1].lower() == 'student' and len(parts) == 3:
                    student = db.get_student(parts[2])
                    print_student(student)

                elif parts[1].lower() == 'discipline' and len(parts) == 3:
                    disciplines = db.get_disciplines_by_course(parts[2])
                    print_disciplines(disciplines)

                elif parts[1].lower() == 'students' and len(parts) == 3:
                    students = db.get_students_by_course(parts[2])
                    print_students(students)

                elif parts[1].lower() == 'disciplines' and len(parts) == 2:
                    disciplines = db.get_all_disciplines()
                    print_disciplines(disciplines)

                else:
                    print("❌ Неверный формат GET команды")

            elif action == 'PUT':
                if parts[1].lower() == 'student' and len(parts) >= 4:
                    # Объединяем имя, если оно состоит из нескольких слов
                    name = ' '.join(parts[2:-1])
                    course = parts[-1]
                    db.add_student(name, course)

                elif parts[1].lower() == 'discipline' and len(parts) >= 6:
                    # Объединяем название дисциплины, если оно состоит из нескольких слов
                    discipline_name = ' '.join(parts[2:-3])
                    day = parts[-3]
                    lesson = parts[-2]
                    course = parts[-1]
                    db.add_discipline(discipline_name, day, lesson, course)

                else:
                    print("❌ Неверный формат PUT команды")
                    print("Пример: PUT student 'Иван Иванов' 1")
                    print("Пример: PUT discipline 'Высшая математика' Понедельник 1 2")

            elif action == 'DELETE':
                if parts[1].lower() == 'student' and len(parts) == 3:
                    db.delete_student(parts[2])

                elif parts[1].lower() == 'discipline' and len(parts) == 3:
                    db.delete_discipline(parts[2])

                else:
                    print("❌ Неверный формат DELETE команды")

            else:
                print("❌ Неизвестная команда")

        except KeyboardInterrupt:
            print("\n👋 Выход из программы...")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")

    db.close_connection()


if __name__ == "__main__":
    main()