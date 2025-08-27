import logging
import sys
import os
import time

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton,
                               QFileDialog, QLabel, QMessageBox, QTableWidget, QAbstractItemView,
                               QHeaderView, QTableWidgetItem)
from PySide6.QtCore import Qt
import json
import kk_card_match_mod as kk_core


class ImageAnalyzerApp(QMainWindow):
    mod_file_name = "kk_mod.json"
    config_file_name = "kk_card_tool_config.json"

    def __init__(self):
        super().__init__()
        self.mod_repository_path = ""
        self.mod_game_path = ""
        self.card_path = ""
        self.results = []
        self.init_ui()
        self.load_config()

    def init_ui(self):
        self.setWindowTitle('KK CARD TOOL')
        self.setGeometry(100, 100, 800, 600)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)

        # 按钮区域
        button_layout = QHBoxLayout()

        # 第一个按钮：选择文件夹1
        self.btn_folder1 = QPushButton('请选择mod仓库路径')
        self.btn_folder1.clicked.connect(self.select_folder1)
        button_layout.addWidget(self.btn_folder1)

        # 初始化或者更新mod仓库json文件
        self.btn_generate_mod_repository_json = QPushButton('初始化或更新mod仓库信息')
        self.btn_generate_mod_repository_json.clicked.connect(self.generate_mod_repository_json)
        button_layout.addWidget(self.btn_generate_mod_repository_json)

        # 第二个按钮：选择文件夹2
        self.btn_folder2 = QPushButton('请选择游戏mod路径')
        self.btn_folder2.clicked.connect(self.select_folder2)
        button_layout.addWidget(self.btn_folder2)

        # 初始化或更新游戏mod的json文件
        self.btn_generate_mod_game_json = QPushButton('初始化或更新游戏mod信息')
        self.btn_generate_mod_game_json.clicked.connect(self.generate_mod_game_json)
        button_layout.addWidget(self.btn_generate_mod_game_json)

        # 第三个按钮：选择图片
        self.btn_image = QPushButton('请选择人物卡')
        self.btn_image.clicked.connect(self.select_image)
        button_layout.addWidget(self.btn_image)

        # 第四个按钮：解析图片
        # self.btn_analyze = QPushButton('获取人物卡mod信息')
        # self.btn_analyze.clicked.connect(self.analyze_image)
        # button_layout.addWidget(self.btn_analyze)

        # 第五个按钮：保存路径
        self.btn_save = QPushButton('保存路径配置信息')
        self.btn_save.clicked.connect(self.save_config)
        button_layout.addWidget(self.btn_save)

        main_layout.addLayout(button_layout)

        # 路径显示区域
        path_layout = QVBoxLayout()

        self.label_folder1 = QLabel('mod仓库路径: 未选择')
        self.label_folder2 = QLabel('游戏mod路径: 未选择')
        self.label_image = QLabel('人物卡路径: 未选择')

        path_layout.addWidget(self.label_folder1)
        path_layout.addWidget(self.label_folder2)
        path_layout.addWidget(self.label_image)

        main_layout.addLayout(path_layout)

        # 解析结果table
        self.setup_table()
        main_layout.addWidget(self.table_widget)

    def setup_table(self):
        """设置表格视图"""
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)  # 两列
        self.table_widget.setHorizontalHeaderLabels(['mod名称', 'mod路径'])

        # 设置表格样式
        self.table_widget.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                border: 1px solid #c0c0c0;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #e0e0e0;
                color: black;
            }
        """)

        # 设置表头样式
        header_style = """
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 8px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """
        self.table_widget.horizontalHeader().setStyleSheet(header_style)
        self.table_widget.verticalHeader().setStyleSheet(header_style)

        # 设置表格属性
        self.table_widget.setShowGrid(True)  # 显示网格线
        self.table_widget.setAlternatingRowColors(True)  # 交替行颜色
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # 设置列宽自适应
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 第一列自适应
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 第二列根据内容调整

    def add_result_item(self, filename, result):
        """向表格中添加解析结果"""
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)

        # 创建表格项
        filename_item = QTableWidgetItem(filename)
        result_item = QTableWidgetItem(result)

        # 设置项的对齐方式
        filename_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        result_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        # 添加到表格
        self.table_widget.setItem(row_position, 0, filename_item)
        self.table_widget.setItem(row_position, 1, result_item)

        # 添加分割线效果 - 通过设置行高和样式来实现
        self.table_widget.setRowHeight(row_position, 35)  # 设置行高

    def select_folder1(self):
        """选择第一个文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "请选择mod仓库路径")
        if folder_path:
            self.mod_repository_path = folder_path
            self.label_folder1.setText(f'mod仓库: {folder_path}')

    def generate_mod_repository_json(self):
        if not self.mod_repository_path:
            QMessageBox.warning(self, "警告", "请先选择mod仓库路径！")
            return
        try:
            kk_core.generate_mod_json_file(self.mod_repository_path,
                                           os.path.join(self.mod_repository_path, self.mod_file_name))
        except Exception as e:
            logging.info("mod仓库json生成失败：{}", e)
            QMessageBox.critical(self, "错误", "mod仓库json生成失败")

    def generate_mod_game_json(self):
        if not self.mod_game_path:
            QMessageBox.warning(self, "警告", "请先选择游戏mod路径！")
            return
        try:
            kk_core.generate_mod_json_file(self.mod_game_path,
                                           os.path.join(self.mod_game_path, self.mod_file_name))
        except Exception as e:
            logging.info("游戏mod信息json生成失败：{}", e)
            QMessageBox.critical(self, "错误", "游戏mod信息json生成失败")

    def select_folder2(self):
        """选择第二个文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "请选择游戏mod文件夹路径")
        if folder_path:
            self.mod_game_path = folder_path
            self.label_folder2.setText(f'游戏mod路径: {folder_path}')

    def select_image(self):
        """选择图片文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.png)"
        )
        if file_path:
            self.card_path = file_path
            self.label_image.setText(f'图片路径: {file_path}')

            self.analyze_image()

    # 加载仓库的mod json数据
    def load_mod_repository_json_file(self):
        with open(os.path.join(self.mod_repository_path, self.mod_file_name), "r", encoding="utf-8") as f:
            return json.load(f)

    # 获取游戏的mod json数据
    def load_mod_game_json_file(self):
        with open(os.path.join(self.mod_game_path, self.mod_file_name), "r", encoding="utf-8") as f:
            return json.load(f)

    def clear_table(self):
        """清空表格数据"""
        self.table_widget.setRowCount(0)

    def analyze_image(self):
        """解析图片的逻辑"""
        try:
            repository_mod_json = self.load_mod_repository_json_file()
        except:
            QMessageBox.critical(self, "错误", "请先生成仓库mod信息")
            return

        try:
            game_mod_json = self.load_mod_game_json_file()
        except:
            QMessageBox.critical(self, "错误", "请先生成仓库mod信息")
            return

        try:
            card_mod_info = kk_core.get_card_mod_info(self.card_path)
            missing_mod_set = card_mod_info - game_mod_json.keys()
            missing_mod_map = {}
            missing_mod_flag = False
            if len(missing_mod_set) == 0:
                logging.info("当前卡片在本游戏mod资源中无缺失")
                QMessageBox.information(self, "success", "当前卡片在本游戏mod资源中无缺失")
            else:
                for mod in missing_mod_set:
                    if mod in repository_mod_json:
                        missing_mod_map[mod] = repository_mod_json.get(mod)['mod_dir']
                    else:
                        missing_mod_map[mod] = "Not Found"
                        missing_mod_flag = True
                # 将结果渲染到列表中
                self.clear_table()
                for mod, mod_dir in missing_mod_map:
                    self.add_result_item(mod, mod_dir)

                if missing_mod_flag:
                    logging.info("仓库中存在当前卡片不存在的mod，请更新仓库mod信息")
                    QMessageBox.warning(self, "提示", "仓库中存在当前卡片不存在的mod，请更新仓库mod信息")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"解析过程中出现错误: {str(e)}")

    def save_config(self):
        """保存文件夹路径信息"""
        if not self.mod_repository_path or not self.mod_game_path:
            QMessageBox.warning(self, "警告", "请先选择两个文件夹！")
            return

        try:
            # 选择保存位置
            config_path = os.path.join(os.getcwd(), self.config_file_name)
            # 准备保存的数据
            data = {
                "mod_repository_path": self.mod_repository_path,
                "mod_game_path": self.mod_game_path,
                "save_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # 这里可以添加时间戳
            }

            # 保存到文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            QMessageBox.information(self, "成功", f"路径信息已保存到: {config_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存过程中出现错误: {str(e)}")

    def load_config(self):
        """启动时读取配置文件，如果存在则加载配置"""
        try:
            config_file = os.path.join(os.getcwd(), self.config_file_name)

            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                # 加载文件夹路径
                if "mod_repository_path" in config_data and os.path.exists(config_data["mod_repository_path"]):
                    self.mod_repository_path = config_data["mod_repository_path"]
                    self.label_folder1.setText(f'mod仓库: {self.mod_repository_path}')

                if "mod_game_path" in config_data and os.path.exists(config_data["mod_game_path"]):
                    self.mod_game_path = config_data["mod_game_path"]
                    self.label_folder2.setText(f'游戏mod路径: {self.mod_game_path}')

                logging.info("配置文件加载成功")
            else:
                logging.info("配置文件不存在，跳过加载")

        except Exception as e:
            logging.info(f"读取配置文件时出错: {str(e)}")
            pass

    def closeEvent(self, event):
        """重写关闭事件，在程序退出前自动保存配置"""
        if self.mod_repository_path or self.mod_game_path:
            reply = QMessageBox.question(
                self,
                "确认退出",
                "是否保存当前路径配置后再退出？",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                self.save_config()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)

    # 设置应用程序样式（可选）
    app.setStyle('Fusion')

    window = ImageAnalyzerApp()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
