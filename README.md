# Správce úkolů - Engeto Python Akademie, projekt 5

CLI aplikace pro správu úkolů s připojením na MySQL databázi.

## Funkce

- Přidání nového úkolu
- Zobrazení aktivních úkolů (stav: nezahájeno, probíhá)
- Aktualizace stavu úkolu
- Odstranění úkolu

## Požadavky

- Python 3.10+
- MySQL server
- Závislosti:
```
pip install mysql-connector-python pytest
```

## Nastavení databáze

Před spuštěním je potřeba mít běžící MySQL server a vytvořenou databázi:

```sql
CREATE DATABASE task_manager;
CREATE DATABASE test_task_manager;  -- pro testy
```

Přihlašovací údaje lze upravit v `pripojeni_db()` v souboru `main.py`.

## Spuštění

```
python main.py
```

## Spuštění testů

```
python -m pytest test_main.py
```

Testy pracují s oddělenou databází `test_task_manager` a po každém testu automaticky smažou testovací data.
