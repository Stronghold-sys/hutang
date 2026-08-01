from unittest.mock import patch


def test_export_report_csv(client, user1_auth_header):
    with patch("app.services.report.ReportService.export_report", return_value=("col1,col2\nval1,val2", "text/csv", "laporan.csv")):
        res = client.get("/api/v1/reports/export?format=csv", headers=user1_auth_header)
        assert res.status_code == 200
        assert "text/csv" in res.headers["content-type"]


def test_export_report_xlsx(client, user1_auth_header):
    with patch("app.services.report.ReportService.export_report", return_value=(b"fake_excel_bytes", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "laporan_utang_piutang.xlsx")):
        res = client.get("/api/v1/reports/export?format=xlsx", headers=user1_auth_header)
        assert res.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in res.headers["content-type"]

