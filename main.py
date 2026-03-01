"""
main.py: pátý projekt do Engeto Online Python Akademie

author: David Horák
email: daviiid739@gmail.com
"""

import sys

import mysql.connector


# --- DATABÁZOVÉ FUNKCE ---
def pripojeni_db():
    """
    Vytvoří a vrátí připojení k MySQL databázi.
    
    Returns:
        mysql.connector.connection: Aktivní připojení k DB, nebo None při chybě.
    """
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1111",
            database="task_manager"
        )
        print("Připojení k databázi bylo úspěšné.")
        return conn

    except mysql.connector.Error as error:
        print(f"Chyba při připojování: {error}")
        return None

def kurzor_handler(sql_prikaz, parametry=None, commit=False, fetch=False):
    """
    Univerzální handler pro SQL operace. Vytvoří připojení, provede dotaz a spojení uzavře.

    Args:
        sql_prikaz (str): SQL dotaz k provedení.
        parametry (tuple, optional): Parametry pro dotaz — ochrana proti SQL injection.
        commit (bool): True pro INSERT / UPDATE / DELETE.
        fetch (bool): True pokud chceš vrátit výsledky SELECT.

    Returns:
        list: Prázdný list při úspěchu bez dat, list řádků při SELECT dotazu.
        None: Při chybě připojení nebo SQL chybě.
    """
    conn = pripojeni_db()

    if conn is None:
        print("Chyba připojení.")
        return None

    cursor = conn.cursor()
    vysledek = []

    try:
        if parametry:
            cursor.execute(sql_prikaz, parametry)
        else:
            cursor.execute(sql_prikaz)

        if commit:
            conn.commit()
            print("SQL příkaz proveden a uložen.")

        if fetch:
            vysledek = cursor.fetchall()

        return vysledek

    except mysql.connector.Error as error:
        print(f"Chyba: {error}")
        return None

    finally:
        cursor.close()
        conn.close()


def vytvoreni_tabulky():
    """
    Ověří existenci tabulky 'ukoly' v databázi.
    Pokud tabulka neexistuje, vytvoří ji s potřebnými sloupci.
    """
    # --- Zkontroluj zda tabulka existuje ---
    sql_kontrola = """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'test'
        AND table_name = 'ukoly'
    """
    kontrola = kurzor_handler(sql_kontrola, fetch=True)

    if kontrola is None:
        return

    if kontrola[0][0] == 1:
        print("Tabulka 'ukoly' již existuje.\n")
        return

    # --- Vytvoř tabulku ---
    print("Vytvářím tabulku 'ukoly'...")

    sql_vytvoreni = """
        CREATE TABLE ukoly (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nazev VARCHAR(100) NOT NULL,
            popis TEXT,
            stav ENUM('nezahájeno', 'probíhá', 'hotovo') DEFAULT 'nezahájeno',
            datum_vytvoreni DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    nova_tabulka = kurzor_handler(sql_vytvoreni)

    if nova_tabulka is not None:
        print("Tabulka 'ukoly' úspěšně vytvořena.\n")


# --- FUNKCE PRO SBĚR A VALIDACI VSTUPŮ OD UŽIVATELE ---
def ziskat_vstup_ukolu() -> tuple:
    """
    Získá název a popis nového úkolu od uživatele přes konzoli.
    Opakuje dotaz dokud uživatel nezadá neprázdný vstup.

    Returns:
        tuple[str, str]: Validní (nazev, popis) zadané uživatelem.
    """
    while True:
        nazev_ukolu = input("Zadejte název úkolu: ").strip()
        if nazev_ukolu:
            break
        print("Název nesmí být prázdný, zadej prosím znovu.\n")

    while True:
        popis_ukolu = input("Zadejte popis úkolu: ").strip()
        if popis_ukolu:
            break
        print("Popis nesmí být prázdný, zadej prosím znovu.\n")

    return nazev_ukolu, popis_ukolu

def ziskat_vstup_aktualizace() -> tuple | None:
    """
    Zobrazí seznam aktivních úkolů a získá od uživatele ID úkolu a nový stav.
    Validuje že zadané ID existuje v seznamu a že nový stav je platná hodnota.

    Returns:
        tuple[int, str]: Validní (id, novy_stav) zadané uživatelem.
        None: Pokud nejsou žádné úkoly k aktualizaci.
    """
    ukoly = zobrazit_ukoly('id', 'nazev', 'stav')

    if not ukoly:
        print("Žádné úkoly k aktualizování.\n")
        return None

    vsechna_id = [ukol[0] for ukol in ukoly]

    while True:
        try:
            zadane_id = int(input("Zadej ID úkolu, který chceš aktualizovat: "))
        except ValueError:
            print("Zadej prosím číslo.\n")
            continue
        
        # --- Validace id ---
        if zadane_id not in vsechna_id:
            print("Neplatné ID, zkus to znovu.\n")
            continue

        break

    nazev_ukolu = [ukol[1] for ukol in ukoly if zadane_id == ukol[0]][0]
    print(f"\nAktualizuješ úkol: {nazev_ukolu}")
    print("Vyber nový stav zadáním čísla, nebo celým slovem:")

    moznosti = {1: "probíhá", 2: "hotovo"}
    for cislo, stav in moznosti.items():
        print(f"{cislo}. {stav}")

    # --- Validace stavu ---
    while True:
        novy_stav = input("Nový stav: ").lower().strip()

        if novy_stav.isdecimal() and int(novy_stav) in moznosti:
            novy_stav = moznosti[int(novy_stav)]
            break
        elif novy_stav in moznosti.values():
            break
        else:
            print("Neplatný vstup, zkus to znovu.\n")

    return zadane_id, novy_stav

def ziskat_vstup_odstraneni() -> int | None:
    """
    Zobrazí seznam aktivních úkolů a získá od uživatele ID úkolu ke smazání.
    Validuje že zadané ID existuje v seznamu.

    Returns:
        int: Validní ID úkolu zadané uživatelem.
        None: Pokud nejsou žádné úkoly k odstranění.
    """
    ukoly = zobrazit_ukoly()

    if not ukoly:
        print("Žádné úkoly k odstranění.\n")
        return None

    vsechna_id = [ukol[0] for ukol in ukoly]

    while True:
        try:
            zadane_id = int(input("Zadej ID úkolu, který chceš odstranit: "))
        except ValueError:
            print("Zadej prosím číslo.\n")
            continue

        if zadane_id not in vsechna_id:
            print("Neplatné ID, zkus to znovu.\n")
            continue

        return zadane_id


# --- TASK MANAGER FUNKCE ---
def pridat_ukol(nazev: str, popis: str) -> None:
    """
    Uloží nový úkol do databáze.
    Úkolu jsou přiřazeny automatické hodnoty: ID a výchozí stav 'nezahájeno'.

    Args (nesmí být prázdné):
        nazev (str): Název úkolu
        popis (str): Popis úkolu

    Raises:
        ValueError: Pokud je název nebo popis prázdný string.
    """
    if not nazev or not nazev.strip():
        raise ValueError("Název úkolu nesmí být prázdný.")

    if not popis or not popis.strip():
        raise ValueError("Popis úkolu nesmí být prázdný.")

    sql_prikaz = "INSERT INTO ukoly (nazev, popis) VALUES (%s, %s)"
    pridani_ukolu = kurzor_handler(sql_prikaz, parametry=(nazev, popis), commit=True)

    if pridani_ukolu is not None:
        print(f"Úkol '{nazev}' byl přidán do DB.\n")


def zobrazit_ukoly(*sloupce) -> list | None:
    """
    Zobrazí všechny úkoly se stavem 'nezahájeno' nebo 'probíhá'.
    Pokud je seznam prázdný, vypíše informační zprávu.

    Args:
        *sloupce (str): Názvy sloupců k zobrazení. Výchozí: id, nazev, popis, stav.

    Returns:
        list: List řádků z DB, nebo None při prázdném výsledku.
    """
    if not sloupce:
        sloupce = ('id', 'nazev', 'popis', 'stav')

    sloupce_str = ", ".join(sloupce)

    sql_prikaz = f"SELECT {sloupce_str} FROM ukoly WHERE NOT stav = 'hotovo'"
    ukoly = kurzor_handler(sql_prikaz, fetch=True)

    if not ukoly:
        print("Žádné úkoly k zobrazení.\n")
        return None

    print("Seznam úkolů:")
    for ukol in ukoly:
        print(" - ".join(str(hodnota) for hodnota in ukol))
    print()

    return ukoly

def aktualizovat_ukol(id: int, novy_stav: str) -> None:
    """
    Aktualizuje stav úkolu v databázi podle zadaného ID.

    Args:
        id (int): ID úkolu k aktualizaci.
        novy_stav (str): Nový stav úkolu — musí být 'probíhá' nebo 'hotovo'.

    Raises:
        ValueError: Pokud nový stav není platná hodnota.
    """
    platne_stavy = ("probíhá", "hotovo")

    if novy_stav not in platne_stavy:
        raise ValueError(f"Neplatný stav '{novy_stav}'. Povolené hodnoty: {platne_stavy}")

    sql = "UPDATE ukoly SET stav = %s WHERE id = %s"
    kurzor_handler(sql, parametry=(novy_stav, id), commit=True)
    print(f"Úkol ID {id} byl aktualizován na stav '{novy_stav}'.\n")

def odstranit_ukol(id: int) -> None:
    """
    Odstraní úkol z databáze podle zadaného ID.

    Args:
        id (int): ID úkolu k odstranění — musí být kladné celé číslo.

    Raises:
        ValueError: Pokud ID není kladné celé číslo.
    """
    if not isinstance(id, int) or id <= 0:
        raise ValueError(f"ID musí být kladné celé číslo, zadáno: {id}")

    sql = "DELETE FROM ukoly WHERE id = %s"
    kurzor_handler(sql, parametry=(id,), commit=True)
    print(f"Úkol ID {id} byl odstraněn.\n")

def konec_programu() -> None:
    """
    Vypíše zprávu o ukončení a ukončí program.
    """
    print("Konec programu.")
    sys.exit(0)


# --- WRAPPER FUNKCE PRO HLAVNÍ MENU ---
def pridat_ukol_wrap() -> None:
    """
    Wrapper pro přidání úkolu — nejdříve získá vstup od uživatele,
    poté zavolá pridat_ukol() s validovanými daty.
    """
    nazev, popis = ziskat_vstup_ukolu()
    try:
        pridat_ukol(nazev, popis)
    except ValueError as e:
        print(f"Chyba: {e}\n")

def aktualizovat_ukol_wrap() -> None:
    """
    Wrapper pro aktualizaci úkolu — nejdříve zobrazí seznam a získá vstup od uživatele,
    poté zavolá aktualizovat_ukol() s validovanými daty.
    """
    vstup = ziskat_vstup_aktualizace()
    if vstup is None:
        return
    
    id, novy_stav = vstup
    try:
        aktualizovat_ukol(id, novy_stav)
    except ValueError as e:
        print(f"Chyba: {e}\n")

def odstranit_ukol_wrap() -> None:
    """
    Wrapper pro odstranění úkolu — nejdříve zobrazí seznam a získá vstup od uživatele,
    poté zavolá odstranit_ukol() s validovaným ID.
    """
    id = ziskat_vstup_odstraneni()
    if id is None:
        return
    try:
        odstranit_ukol(id)
    except ValueError as e:
        print(f"Chyba: {e}\n")


# --- HLAVNÍ MENU ---
def hlavni_menu() -> None:
    """
    Zobrazí hlavní menu programu a zpracovává volby uživatele.
    Při spuštění ověří existenci tabulky v DB a případně ji vytvoří.
    Volá příslušné wrapper funkce na základě uživatelova výběru.
    """
    vytvoreni_tabulky()

    moznosti = {
        1: ("Přidat nový úkol",     pridat_ukol_wrap),
        2: ("Zobrazit všechny úkoly", zobrazit_ukoly),
        3: ("Aktualizovat úkol",    aktualizovat_ukol_wrap),
        4: ("Odstranit úkol",       odstranit_ukol_wrap),
        5: ("Konec programu",       konec_programu)
    }

    while True:
        print("Správce úkolů - Hlavní menu")

        for cislo, (nazev_funkce, _) in moznosti.items():
            print(f"{cislo}. {nazev_funkce}")

        vybrana_moznost = input(f"Vyberte možnost (1-{len(moznosti)}): ")
        print()

        if vybrana_moznost.isdecimal() and int(vybrana_moznost) in moznosti:
            _, funkce = moznosti[int(vybrana_moznost)]
            funkce()
        else:
            print("Neplatná volba, zkus to znovu.\n")


if __name__ == "__main__":
    hlavni_menu()