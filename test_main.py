"""
test_main.py: Testy pro pátý projekt do Engeto Online Python Akademie

author: David Horák
email: daviiid739@gmail.com
"""

from unittest.mock import patch

import mysql.connector
import pytest

from main import pridat_ukol, aktualizovat_ukol, odstranit_ukol


# --- FIXTURES ---
@pytest.fixture
def testovaci_db():
    """
    Fixture která vytvoří nové připojení k testovací databázi.
    Po skončení testu připojení zavře.

    Yields:
        mysql.connector.connection: Aktivní připojení k testovací DB.
    """
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1111",
        database="test_task_manager"
    )
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def vytvor_a_vycisti_tabulku(testovaci_db):
    """
    Fixture která před každým testem vytvoří tabulku 'ukoly' pokud neexistuje,
    a po každém testu smaže všechna testovací data.
    autouse=True zajistí že se spustí automaticky pro každý test.

    Args:
        testovaci_db: Fixture s připojením k testovací DB.
    """
    cursor = testovaci_db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ukoly (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nazev VARCHAR(100) NOT NULL,
            popis TEXT,
            stav ENUM('nezahájeno', 'probíhá', 'hotovo') DEFAULT 'nezahájeno',
            datum_vytvoreni DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    testovaci_db.commit()
    cursor.close()

    yield

    # kursor_handler zavírá připojení - proto je třeba .reconnect()
    testovaci_db.reconnect()        # obnov připojení 
    cursor = testovaci_db.cursor()
    cursor.execute("TRUNCATE TABLE ukoly")
    cursor.close()


@pytest.fixture(autouse=True)
def nahrad_pripojeni_db(testovaci_db):
    """
    Fixture která nahradí pripojeni_db() v main.py připojením k testovací DB pro každý test.

    Args:
        testovaci_db: Fixture s připojením k testovací DB.
    """
    with patch('main.pripojeni_db', return_value=testovaci_db):
        yield


@pytest.fixture
def existujici_ukol(testovaci_db):
    """
    Pomocná fixture která vloží testovací úkol do DB a vrátí jeho ID.
    Používá se v testech kde potřebujeme existující záznam.

    Args:
        testovaci_db: Fixture s připojením k testovací DB.

    Returns:
        int: ID vloženého úkolu.
    """
    cursor = testovaci_db.cursor()
    cursor.execute(
        "INSERT INTO ukoly (nazev, popis) VALUES (%s, %s)",
        ("Testovací úkol", "Popis testovacího úkolu")
    )
    testovaci_db.commit()
    ukol_id = cursor.lastrowid
    cursor.close()
    return ukol_id


# --- TESTY - pridat_ukol() ---
def test_pridat_ukol_pozitivni(testovaci_db):
    """
    Pozitivní test: Validní název a popis se uloží do DB.
    Ověřuje že po zavolání pridat_ukol() existuje záznam v tabulce.
    """
    pridat_ukol("Testovací úkol", "Popis testovacího úkolu")

    testovaci_db.reconnect()        # obnov připojení
    cursor = testovaci_db.cursor()
    cursor.execute("SELECT nazev, popis FROM ukoly WHERE nazev = 'Testovací úkol'")
    vysledek = cursor.fetchone()
    cursor.close()

    assert vysledek is not None, "Úkol by měl existovat v DB"
    assert vysledek[0] == "Testovací úkol"
    assert vysledek[1] == "Popis testovacího úkolu"


def test_pridat_ukol_negativni_prazdny_nazev():
    """
    Negativní test: Prázdný název vyvolá ValueError.
    Ověřuje že funkce odmítne prázdný string a nevloží nic do DB.
    """
    with pytest.raises(ValueError, match="Název úkolu nesmí být prázdný"):
        pridat_ukol("", "Popis úkolu")


# --- TESTY - aktualizovat_ukol() ---
def test_aktualizovat_ukol_pozitivni(testovaci_db, existujici_ukol):
    """
    Pozitivní test: Platný stav 'hotovo' se uloží do DB.
    Ověřuje že po zavolání aktualizovat_ukol() má záznam správný stav.
    """
    aktualizovat_ukol(existujici_ukol, "hotovo")

    testovaci_db.reconnect()        # obnov připojení
    cursor = testovaci_db.cursor()
    cursor.execute("SELECT stav FROM ukoly WHERE id = %s", (existujici_ukol,))
    vysledek = cursor.fetchone()
    cursor.close()

    assert vysledek is not None
    assert vysledek[0] == "hotovo"


def test_aktualizovat_ukol_negativni_neplatny_stav(existujici_ukol):
    """
    Negativní test: Neplatný stav vyvolá ValueError.
    Ověřuje že funkce odmítne stav který není v povolených hodnotách.
    """
    with pytest.raises(ValueError, match="Neplatný stav"):
        aktualizovat_ukol(existujici_ukol, "neexistujici_stav")


# --- TESTY - odstranit_ukol() ---
def test_odstranit_ukol_pozitivni(testovaci_db, existujici_ukol):
    """
    Pozitivní test: Úkol s platným ID se odstraní z DB.
    Ověřuje že po zavolání odstranit_ukol() záznam v DB neexistuje.
    """
    odstranit_ukol(existujici_ukol)

    testovaci_db.reconnect()        # obnov připojení
    cursor = testovaci_db.cursor()
    cursor.execute("SELECT id FROM ukoly WHERE id = %s", (existujici_ukol,))
    vysledek = cursor.fetchone()
    cursor.close()

    assert vysledek is None, "Úkol by neměl existovat v DB po odstranění"


def test_odstranit_ukol_negativni_neplatne_id():
    """
    Negativní test: Neplatné ID (záporné číslo) vyvolá ValueError.
    Ověřuje že funkce odmítne ID které nemůže existovat v DB.
    """
    with pytest.raises(ValueError, match="ID musí být kladné celé číslo"):
        odstranit_ukol(-1)