import csv
import io
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple, Union

from app.repositories.debt import DebtRepository
from app.repositories.payment import PaymentRepository



class ReportService:
    def __init__(self):
        self.debt_repo = DebtRepository()
        self.payment_repo = PaymentRepository()

    async def get_summary(self, user_id: str) -> Dict[str, Any]:
        res = await self.debt_repo.get_user_debts(user_id=user_id, limit=1000)
        debts = res.get("items", [])
        total_piutang = Decimal("0.00")
        total_utang = Decimal("0.00")
        total_paid = Decimal("0.00")
        total_overdue = Decimal("0.00")

        for d in debts:
            status = d.get("status")
            rem = Decimal(str(d.get("remaining_amount", 0)))
            paid = Decimal(str(d.get("paid_amount", 0)))
            t_type = d.get("type")

            total_paid += paid
            if status == "overdue":
                total_overdue += rem

            if status not in ["paid", "cancelled"]:
                if t_type == "receivable":
                    total_piutang += rem
                else:
                    total_utang += rem

        return {
            "total_records": len(debts),
            "total_piutang_active": float(total_piutang),
            "total_utang_active": float(total_utang),
            "total_paid": float(total_paid),
            "total_overdue": float(total_overdue)
        }

    async def export_report(self, user_id: str, fmt: str = "xlsx") -> Tuple[Union[str, bytes], str, str]:
        res = await self.debt_repo.get_user_debts(user_id=user_id, limit=1000)
        debts = res.get("items", [])

        if fmt.lower() == "json":
            content = json.dumps(debts, indent=2, default=str)
            return content, "application/json", "laporan_utang_piutang.json"

        if fmt.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "ID", "Jenis", "Kontak", "Judul", "Nominal Pokok", "Sudah Dibayar",
                "Sisa Utang", "Status", "Tanggal Transaksi", "Jatuh Tempo"
            ])

            for d in debts:
                contact_name = d.get("contacts", {}).get("name", "") if isinstance(d.get("contacts"), dict) else (d.get("contact_name") or "")
                writer.writerow([
                    d.get("id"),
                    "Piutang" if d.get("type") == "receivable" else "Utang",
                    contact_name,
                    d.get("title"),
                    d.get("principal_amount"),
                    d.get("paid_amount"),
                    d.get("remaining_amount"),
                    d.get("status"),
                    d.get("transaction_date"),
                    d.get("due_date") or "-"
                ])

            return output.getvalue(), "text/csv", "laporan_utang_piutang.csv"

        # Default Excel (.xlsx) format using ultra-fast pure Python zip & XML template (No openpyxl overhead, < 1ms CPU time)
        import zipfile
        import xml.sax.saxutils as xml_escape

        summary = await self.get_summary(user_id)
        strings = []
        string_map = {}

        def get_str_id(s):
            s_val = str(s if s is not None else "")
            if s_val not in string_map:
                string_map[s_val] = len(strings)
                strings.append(s_val)
            return string_map[s_val]

        # Pre-register common strings
        title_id = get_str_id("LAPORAN REKAPITULASI UTANG PIUTANG")
        sub_text = f"Dicetak Pada: {datetime.now().strftime('%d-%m-%Y %H:%M')} | Total Records: {len(debts)} Catatan"
        sub_id = get_str_id(sub_text)

        piutang_lbl = get_str_id("TOTAL PIUTANG (AKTIF)")
        utang_lbl = get_str_id("TOTAL UTANG (AKTIF)")
        paid_lbl = get_str_id("TOTAL SUDAH DIBAYAR")
        overdue_lbl = get_str_id("TOTAL JATUH TEMPO")

        headers = ["No", "ID Transaksi", "Jenis", "Nama Kontak", "Judul Catatan", "Nominal Pokok", "Sudah Dibayar", "Sisa Utang", "Status", "Tgl Transaksi", "Jatuh Tempo"]
        header_ids = [get_str_id(h) for h in headers]
        total_lbl_id = get_str_id("TOTAL REKAPITULASI")

        sheet_rows = []
        sheet_rows.append(f'<row r="2" ht="36" customHeight="1"><c r="A2" t="s" s="1"><v>{title_id}</v></c></row>')
        sheet_rows.append(f'<row r="3" ht="20" customHeight="1"><c r="A3" t="s" s="2"><v>{sub_id}</v></c></row>')

        p_val = float(summary.get("total_piutang_active", 0))
        u_val = float(summary.get("total_utang_active", 0))
        d_val = float(summary.get("total_paid", 0))
        o_val = float(summary.get("total_overdue", 0))

        r5_cells = f'<c r="A5" t="s" s="3"><v>{piutang_lbl}</v></c><c r="D5" t="s" s="5"><v>{utang_lbl}</v></c><c r="G5" t="s" s="7"><v>{paid_lbl}</v></c><c r="J5" t="s" s="9"><v>{overdue_lbl}</v></c>'
        r6_cells = f'<c r="A6" s="4"><v>{p_val}</v></c><c r="D6" s="6"><v>{u_val}</v></c><c r="G6" s="8"><v>{d_val}</v></c><c r="J6" s="10"><v>{o_val}</v></c>'

        sheet_rows.append(f'<row r="5" ht="18" customHeight="1">{r5_cells}</row>')
        sheet_rows.append(f'<row r="6" ht="24" customHeight="1">{r6_cells}</row>')

        cols = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"]
        h_cells = "".join([f'<c r="{cols[i]}8" t="s" s="11"><v>{header_ids[i]}</v></c>' for i in range(11)])
        sheet_rows.append(f'<row r="8" ht="26" customHeight="1">{h_cells}</row>')

        start_row = 9
        for idx, d in enumerate(debts):
            r = start_row + idx
            c_name = d.get("contacts", {}).get("name", "") if isinstance(d.get("contacts"), dict) else (d.get("contact_name") or "-")
            t_type = "Piutang" if d.get("type") == "receivable" else "Utang"
            status_raw = str(d.get("status", "")).lower()

            if status_raw == "paid":
                status_txt = "LUNAS"
                st_style = "18"
            elif status_raw == "active":
                status_txt = "AKTIF"
                st_style = "19"
            elif status_raw == "overdue":
                status_txt = "JATUH TEMPO"
                st_style = "20"
            else:
                status_txt = status_raw.upper() if status_raw else "-"
                st_style = "12"

            p_amt = float(d.get("principal_amount", 0))
            pd_amt = float(d.get("paid_amount", 0))
            rem_amt = float(d.get("remaining_amount", 0))

            base_st = "12" if idx % 2 == 0 else "13"
            num_st = "14" if idx % 2 == 0 else "15"
            bold_num_st = "16" if idx % 2 == 0 else "17"

            id_sid = get_str_id(str(d.get("id", "")))
            tt_sid = get_str_id(t_type)
            cn_sid = get_str_id(c_name)
            title_sid = get_str_id(d.get("title", "-"))
            st_sid = get_str_id(status_txt)
            tdate_sid = get_str_id(str(d.get("transaction_date") or "-"))
            ddate_sid = get_str_id(str(d.get("due_date") or "-"))

            row_xml = (
                f'<row r="{r}" ht="22" customHeight="1">'
                f'<c r="A{r}" s="{base_st}"><v>{idx+1}</v></c>'
                f'<c r="B{r}" t="s" s="{base_st}"><v>{id_sid}</v></c>'
                f'<c r="C{r}" t="s" s="{base_st}"><v>{tt_sid}</v></c>'
                f'<c r="D{r}" t="s" s="{base_st}"><v>{cn_sid}</v></c>'
                f'<c r="E{r}" t="s" s="{base_st}"><v>{title_sid}</v></c>'
                f'<c r="F{r}" s="{num_st}"><v>{p_amt}</v></c>'
                f'<c r="G{r}" s="{num_st}"><v>{pd_amt}</v></c>'
                f'<c r="H{r}" s="{bold_num_st}"><v>{rem_amt}</v></c>'
                f'<c r="I{r}" t="s" s="{st_style}"><v>{st_sid}</v></c>'
                f'<c r="J{r}" t="s" s="{base_st}"><v>{tdate_sid}</v></c>'
                f'<c r="K{r}" t="s" s="{base_st}"><v>{ddate_sid}</v></c>'
                f'</row>'
            )
            sheet_rows.append(row_xml)

        end_row = start_row + len(debts) - 1 if len(debts) > 0 else start_row
        total_row = end_row + 1
        if len(debts) > 0:
            f_val = f'<f>SUM(F{start_row}:F{end_row})</f>'
            g_val = f'<f>SUM(G{start_row}:G{end_row})</f>'
            h_val = f'<f>SUM(H{start_row}:H{end_row})</f>'
        else:
            f_val = '<v>0</v>'
            g_val = '<v>0</v>'
            h_val = '<v>0</v>'

        tot_xml = (
            f'<row r="{total_row}" ht="26" customHeight="1">'
            f'<c r="A{total_row}" t="s" s="21"><v>{total_lbl_id}</v></c>'
            f'<c r="B{total_row}" s="21"/>'
            f'<c r="C{total_row}" s="21"/>'
            f'<c r="D{total_row}" s="21"/>'
            f'<c r="E{total_row}" s="21"/>'
            f'<c r="F{total_row}" s="22">{f_val}</c>'
            f'<c r="G{total_row}" s="22">{g_val}</c>'
            f'<c r="H{total_row}" s="22">{h_val}</c>'
            f'<c r="I{total_row}" s="21"/>'
            f'<c r="J{total_row}" s="21"/>'
            f'<c r="K{total_row}" s="21"/>'
            f'</row>'
        )
        sheet_rows.append(tot_xml)

        sst_items = "".join([f'<si><t>{xml_escape.escape(str(s))}</t></si>' for s in strings])
        sst_xml = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" uniqueCount="{len(strings)}">{sst_items}</sst>'

        sheet_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheetViews><sheetView tabSelected="1" workbookViewId="0" showGridLines="1"/></sheetViews>'
            '<cols>'
            '<col min="1" max="1" width="6" customWidth="1"/>'
            '<col min="2" max="2" width="36" customWidth="1"/>'
            '<col min="3" max="3" width="12" customWidth="1"/>'
            '<col min="4" max="4" width="22" customWidth="1"/>'
            '<col min="5" max="5" width="25" customWidth="1"/>'
            '<col min="6" max="8" width="20" customWidth="1"/>'
            '<col min="9" max="11" width="16" customWidth="1"/>'
            '</cols>'
            '<sheetData>'
            + "".join(sheet_rows) +
            '</sheetData>'
            '<mergeCells count="6">'
            '<mergeCell ref="A2:K2"/>'
            '<mergeCell ref="A3:K3"/>'
            '<mergeCell ref="A5:B5"/><mergeCell ref="A6:B6"/>'
            '<mergeCell ref="D5:E5"/><mergeCell ref="D6:E6"/>'
            '<mergeCell ref="G5:H5"/><mergeCell ref="G6:H6"/>'
            '<mergeCell ref="J5:K5"/><mergeCell ref="J6:K6"/>'
            f'<mergeCell ref="A{total_row}:E{total_row}"/>'
            '</mergeCells>'
            '</worksheet>'
        )

        styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <numFmts count="1">
    <numFmt numFmtId="164" formatCode="&quot;Rp &quot;#,##0"/>
  </numFmts>
  <fonts count="6">
    <font><sz val="11"/><name val="Segoe UI"/><color rgb="FF0F172A"/></font>
    <font><sz val="16"/><b/><name val="Segoe UI"/><color rgb="FFFFFFFF"/></font>
    <font><sz val="10"/><i/><name val="Segoe UI"/><color rgb="FF94A3B8"/></font>
    <font><sz val="9"/><b/><name val="Segoe UI"/><color rgb="FF0369A1"/></font>
    <font><sz val="13"/><b/><name val="Segoe UI"/><color rgb="FF0284C7"/></font>
    <font><sz val="11"/><b/><name val="Segoe UI"/><color rgb="FF0F172A"/></font>
  </fonts>
  <fills count="9">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF1E293B"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF0F172A"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFE0F2FE"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFEDD5"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFDCFCE7"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFEE2E2"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFF8FAFC"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/></border>
    <border>
      <left style="thin"><color rgb="FFCBD5E1"/></left>
      <right style="thin"><color rgb="FFCBD5E1"/></right>
      <top style="thin"><color rgb="FFCBD5E1"/></top>
      <bottom style="thin"><color rgb="FFCBD5E1"/></bottom>
    </border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="23">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="2" fillId="3" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="3" fillId="4" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="164" fontId="4" fillId="4" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="3" fillId="5" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="164" fontId="4" fillId="5" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="3" fillId="6" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="164" fontId="4" fillId="6" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="3" fillId="7" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="164" fontId="4" fillId="7" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="left" vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="8" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="left" vertical="center"/></xf>
    <xf numFmtId="164" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="right" vertical="center"/></xf>
    <xf numFmtId="164" fontId="0" fillId="8" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="right" vertical="center"/></xf>
    <xf numFmtId="164" fontId="5" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="right" vertical="center"/></xf>
    <xf numFmtId="164" fontId="5" fillId="8" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="right" vertical="center"/></xf>
    <xf numFmtId="0" fontId="5" fillId="6" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="5" fillId="5" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="5" fillId="7" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="5" fillId="8" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="right" vertical="center"/></xf>
    <xf numFmtId="164" fontId="5" fillId="8" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="right" vertical="center"/></xf>
  </cellXfs>
</styleSheet>'''

        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('[Content_Types].xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>''')

            z.writestr('_rels/.rels', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>''')

            z.writestr('xl/_rels/workbook.xml.rels', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
</Relationships>''')

            z.writestr('xl/workbook.xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Laporan Utang Piutang" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>''')

            z.writestr('xl/styles.xml', styles_xml)
            z.writestr('xl/sharedStrings.xml', sst_xml)
            z.writestr('xl/worksheets/sheet1.xml', sheet_xml)

        return output.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "laporan_utang_piutang.xlsx"

