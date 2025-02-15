Sub ColorTableBasedOnColumnD()
    Dim ws As Worksheet
    Dim tblRange As Range
    Dim cell As Range
    Dim css_colors_dict As Object
    Dim rankColor As String
    Dim bkgColor As String
    Dim baseKey As String
    Dim sheetNames As Variant
    Dim sheetName As Variant

    ' List of sheet names to apply the coloring
    sheetNames = Array("Sheet1", "Sheet2")

    ' Create the color dictionary
    Set css_colors_dict = CreateObject("Scripting.Dictionary")
    css_colors_dict.Add "S", Array(RGB(255, 153, 0), RGB(255, 204, 0)) ' S_rank, S_bkg
    css_colors_dict.Add "A", Array(RGB(204, 153, 255), RGB(232, 209, 255)) ' A_rank, A_bkg
    css_colors_dict.Add "B", Array(RGB(102, 255, 153), RGB(153, 255, 153)) ' B_rank, B_bkg
    css_colors_dict.Add "C", Array(RGB(83, 210, 255), RGB(204, 236, 255)) ' C_rank, C_bkg
    css_colors_dict.Add "D", Array(RGB(166, 166, 166), RGB(196, 196, 196)) ' D_rank, D_bkg
    css_colors_dict.Add "I", Array(RGB(166, 166, 166), RGB(196, 196, 196)) ' I_rank, I_bkg
    css_colors_dict.Add "-", Array(RGB(166, 166, 166), RGB(196, 196, 196))
    css_colors_dict.Add "A+", Array(RGB(204, 102, 255), RGB(232, 209, 255)) ' A+_rank, uses A_bkg
    css_colors_dict.Add "B+", Array(RGB(0, 255, 0), RGB(153, 255, 153)) ' B+_rank, uses B_bkg
    css_colors_dict.Add "C+", Array(RGB(25, 211, 255), RGB(204, 236, 255)) ' C+_rank, uses C_bkg

    ' Loop through each sheet
    For Each sheetName In sheetNames
        Set ws = ThisWorkbook.Sheets(sheetName) ' Set the current worksheet
        Set tblRange = ws.Range("C1:I1000") ' Adjust range if needed

        ' Loop through each cell in column D (4th column of tblRange)
        For Each cell In tblRange.Columns(2).Cells
            If css_colors_dict.exists(cell.Value) Then
                ' Determine the base key for background color if "X+" case
                If InStr(cell.Value, "+") > 0 Then
                    baseKey = Left(cell.Value, Len(cell.Value) - 1) ' Strip "+" for bkg
                Else
                    baseKey = cell.Value
                End If

                ' Get the rank and background colors
                rankColor = css_colors_dict(cell.Value)(0) ' Rank color
                bkgColor = css_colors_dict(baseKey)(1) ' Background color based on baseKey

                With cell.Offset(0, -1).Resize(1, 7)
                    .Interior.Color = bkgColor
                    .Font.Color = RGB(0, 0, 0) ' Set text color to black
                    ApplyThinBlackBorders .borders
                End With

                ' Apply the rank color to column D (cell itself)
                cell.Interior.Color = rankColor
                cell.Font.Color = RGB(0, 0, 0) ' Set text color to black
                cell.Font.Bold = True
                cell.Font.Size = 11
                ApplyThinBlackBorders cell.borders
            ' Else: font color to white and background black
            Else
                With cell.Offset(0, -1).Resize(1, 7)
                    .Interior.Color = RGB(0, 0, 0) ' Black color
                    .Font.Color = RGB(255, 255, 255) ' White color
                End With
            End If
        Next cell
    Next sheetName
End Sub

' Subroutine to apply thin black borders
Sub ApplyThinBlackBorders(borders As borders)
    Dim border As Integer
    For border = xlEdgeLeft To xlInsideHorizontal
        With borders(border)
            .LineStyle = xlContinuous
            .Weight = xlThin
            .Color = RGB(0, 0, 0) ' Black color
        End With
    Next border
End Sub