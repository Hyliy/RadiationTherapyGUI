import os
import re
import sys

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QAbstractItemView, QTableWidgetItem
from PyQt5.uic import loadUi
from collections import defaultdict
import pandas as pd
import plotly.io as pio


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('./gui-ver2.ui', self)

        self.num_cols = 4
        self.tb.setDragEnabled(True)
        self.tb.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.pattern = re.compile(r'.*(patient(\d+)).*')
        self.dvh_plots = {}

        self.LoadFigs.triggered.connect(self.load_figs)
        self.Save.triggered.connect(self.save_file)
        self.LoadTable.triggered.connect(self.load_table)
        self.tb.cellDoubleClicked.connect(self.cell_selection)

    def load_figs(self):
        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            folder = dialog.selectedFiles()[0]
            if folder:
                for f in sorted(os.listdir(folder), key=lambda x: int(self.pattern.match(x)[2])):
                    if 'json' in f:
                        fig = open(os.path.join(folder, f), 'r')
                        fig = pio.from_json(fig.read())
                        self.dvh_plots[self.pattern.match(f)[1]] = fig

        self.tb.setRowCount(0)
        for r, (k, v) in enumerate(self.dvh_plots.items()):
            self.tb.insertRow(r)
            for c in range(self.num_cols):
                if c == 0:
                    item = QTableWidgetItem(k)
                else:
                    item = QTableWidgetItem('')
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.tb.setItem(r, c, item)

    def save_file(self):
        rows = self.tb.rowCount()
        cols = self.tb.columnCount()
        col_names = ['Patient', 'O < R', 'O > R', 'O = R']

        if rows > 0:
            f = QtWidgets.QFileDialog().getSaveFileName()[0]
            f += '.csv' if '.csv' not in f else ''
            df = pd.DataFrame(columns=col_names)
            for r in range(rows):
                tmp = defaultdict(list)
                for c in range(cols):
                    item = self.tb.item(r, c)
                    if item:
                        tmp[col_names[c]].append(item.text())
                    else:
                        tmp[col_names[c]].append('')
                df = df.append(pd.DataFrame(tmp))

            df = pd.DataFrame(df)
            df.to_csv(f, index=False)

    def load_table(self):
        dialog = QtWidgets.QFileDialog()
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            f = dialog.selectedFiles()[0]
            if f:
                self.tb.setRowCount(0)
                df = pd.read_csv(f)
                df.fillna('', inplace=True)
                for r, row in df.iterrows():
                    self.tb.insertRow(r)
                    for c, value in enumerate(row):
                        item = QTableWidgetItem(value)
                        item.setTextAlignment(QtCore.Qt.AlignCenter)
                        self.tb.setItem(r, c, item)

                        if c == 0:
                            f = os.path.join('./dvh-plots', value + '.json')
                            fig = open(f, 'r')
                            fig = pio.from_json(fig.read())
                            self.dvh_plots[value] = fig
        return

    def cell_selection(self):
        r, c = self.tb.currentRow(), self.tb.currentColumn()
        visited = set()

        def unchecked(col, cur):
            if col < 1 or col > 3 or col in visited:
                return

            item = self.tb.item(r, col)
            visited.add(col)
            if item and item.text() == 'x' and col != cur:
                item.setText('')
            elif col != cur:
                item = QTableWidgetItem('')
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.tb.setItem(r, col, item)

            unchecked(col - 1, cur)
            unchecked(col + 1, cur)

        if 1 <= c <= 3:
            item = self.tb.currentItem()
            if not item:
                item = QTableWidgetItem('x')
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.tb.setItem(r, c, item)
                unchecked(c, c)
            else:
                item.setText('x' if item.text() == '' else '')
                unchecked(c, c)
        else:
            key = self.tb.item(r, c).text()
            self.dvh_plots[key].show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainwindow = MainWindow()
    widget = QtWidgets.QStackedWidget()
    widget.addWidget(mainwindow)
    widget.show()

    sys.exit(app.exec_())

    # try:
    #     sys.exit(app.exec_())
    # except:
    #     print('exiting')
