' To put as code in sheet1
Sub Worksheet_Change(ByVal Target As Range)
    ' Check if the change is in column D
    If Not Intersect(Target, Me.Columns("D")) Is Nothing Then
        ' Loop through each cell in the target range
        Dim cell As Range
        For Each cell In Target
            ' Update the corresponding cell in Sheet2
            ThisWorkbook.Sheets("Sheet2").Cells(cell.Row, cell.Column).Value = cell.Value
        Next cell
    End If
End Sub

