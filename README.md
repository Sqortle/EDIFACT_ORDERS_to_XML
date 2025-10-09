# EDIFACT (ORDERS) to XML Converter

This Python script implements the `XMLConverter` class, an object-oriented solution for transforming raw **EDIFACT ORDERS** messages into a structured XML format. It extracts critical order details, line items, and pricing information, ensuring the output XML is clean and hierarchical.

## Important Note

This converter is specifically configured to process the **ORDERS** EDIFACT message type, as reflected by setting the output root tag:

```python
ET.SubElement(schedule, "SUPP_SCHED_TYPE").text = "ORDERS"
```

## Features

  * **ORDERS Message Support:** Specialized mapping for common segments found in EDIFACT purchase order messages (`LIN`, `PIA`, `IMD`, `QTY`, `PRI`).
  * **Detailed Line Item Creation:** For every `LIN` segment, it creates both an `<ARTICLE_LINE>` and a corresponding `<SCHEDULE_LINE>` to hold detailed item and quantity information.
  * **Party Mapping:** Extracts and maps various party identifiers (`NAD` segments) including **Vendor**, **Buyer**, **Delivery Party**, and **Invoice Party**.
  * **Data Integrity:** Includes robust methods (`sanitize`, `safe_split_component`) to ensure data extracted from complex EDIFACT elements is clean and formatted correctly.
  * **Formatted Output:** Uses a custom `indent` function to generate human-readable XML.
  * **Single File Output:** Converts the entire input EDIFACT message into a single `output.xml` file.

-----

## Prerequisites

  * **Python 3:** The script requires Python 3.
  * **Built-in Libraries:** Only uses the standard `xml.etree.ElementTree` library.

## How to Run the Script

### 1\. Configure Input

1.  Save the Python code as a file (e.g., `edifact.py`).

2.  Paste your raw EDIFACT ORDERS message into the `edifact_message` multiline string at the end of the script. The example placeholder is shown below:

    ```python
    edifact_message = """
    # Paste your raw EDIFACT content here, e.g.:
    UNB+...
    BGM+...
    NAD+BY+BUYER_ID'
    LIN+...
    QTY+1:100'
    ...
    """
    ```

### 2\. Execution

Run the script from your terminal:

```bash
python3 edifact.py
```

### 3\. Output

The script will generate a single XML file named **`output.xml`** in the `Documents` directory:

```
Documents/output.xml
```

-----

## Key Segment Mappings

The `SegmentsClass` handles the transformation of specific EDIFACT data elements into XML tags:

| EDIFACT Segment | XML Tag(s) Created / Updated | Description |
| :--- | :--- | :--- |
| `NAD` | `VENDOR_NO`, `BUYER_NO`, `DELIVERY_PARTY_NO`, `INVOICE_PARTY_NO` | Extracts party identifiers based on qualifiers (`SU`, `BY`, `DP`, `IV`). |
| `BGM` | `MESSAGE_ID` | Extracts the order or message number. |
| `DTM` | `VALID_FROM`, `VALID_UNTIL` | Extracts header-level dates using qualifiers `137` and `2`. |
| `RFF` | `SUPPLIER_REF` | Extracts the main reference number. |
| `LIN` | `<ARTICLE_LINE>`, `<SCHEDULE_LINE>` | Initiates a new line item and assigns a sequential `SCHEDULE_NO`. |
| `PIA` | `PART_NO` (in both article and schedule lines) | Extracts the part number (using qualifier `BP`). |
| `IMD` | `DESCRIPTION` | Extracts the product description. |
| `QTY` | `LAST_RECEIPT_QTY`, `QUANTITY_DUE` | Extracts the quantity value and maps it to both fields for simplicity in the ORDERS context. |
| `PRI` | `UNIT_PRICE` | Extracts the item's unit price. |
