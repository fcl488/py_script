import logging
import shutil
import sys
import os
import time

from PySide6.QtGui import QShortcut, QKeySequence, QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton,
                               QFileDialog, QLabel, QMessageBox, QTableWidget, QAbstractItemView,
                               QHeaderView, QTableWidgetItem, QMenu, QSizePolicy)
from PySide6.QtCore import Qt, QPoint
import json
import kk_card_match_mod as kk_core


class ImageAnalyzerApp(QMainWindow):
    mod_file_name = "kk_mod.json"
    config_file_name = "kk_card_tool_config.json"

    def __init__(self):
        super().__init__()
        self.logger = None
        self.mod_repository_path = ""
        self.mod_game_path = ""
        self.mod_repository_data_cache = None
        self.mod_game_data_cache = None
        self.card_path = ""
        self.current_card_mod_map = {}
        self.missing_mod_map = {}
        self.results = []
        self.setup_logging()
        self.init_ui()
        self.load_config()

    def setup_logging(self):

        # 清除之前的日志处理器
        logging.getLogger().handlers.clear()

        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # 创建处理器列表
        handlers = []

        # 总是添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

        log_path = None

        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            base_dir = os.path.dirname(sys.executable)
            # 使用固定的日志文件名
            log_filename = 'kk_card_tool.log'
            log_path = os.path.join(base_dir, log_filename)

            # 创建文件处理器（追加模式）
            file_handler = logging.FileHandler(log_path, encoding='utf-8', mode='a')
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)

        # 配置logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )

        self.logger = logging.getLogger('KK_CARD_TOOL')

        self.logger.info('=' * 60)
        self.logger.info('KK CARD TOOL START')
        if getattr(sys, 'frozen', False):
            self.logger.info(f'RUNNING ACTIVE: EXE')
            self.logger.info(f'LOG PATH: {log_path}')
        else:
            self.logger.info(f'RUNNING ACTIVE: 脚本')
            self.logger.info(f'LOG OUT: TERMINAL')
        self.logger.info('=' * 60)

    def init_ui(self):
        self.setWindowTitle('KK CARD TOOL')
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('favicon.ico'))

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

        # 按钮区域2
        button_layout2 = QHBoxLayout()
        # 靠右
        button_layout2.setAlignment(Qt.AlignRight)
        # 一键复制mod按钮
        self.btn_cp_mod = QPushButton('一键复制缺失mod')
        self.btn_cp_mod.clicked.connect(self.cp_mod)
        self.btn_cp_mod.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred))
        self.btn_cp_mod.setMinimumWidth(120)
        button_layout2.addWidget(self.btn_cp_mod)
        main_layout.addLayout(button_layout2)

        # 展示当前卡片的mod信息
        self.btn_show_mod = QPushButton('展示卡片mod信息')
        self.btn_show_mod.clicked.connect(self.show_current_card_mod_info)
        self.btn_show_mod.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred))
        self.btn_show_mod.setMinimumWidth(120)
        button_layout2.addWidget(self.btn_show_mod)
        main_layout.addLayout(button_layout2)

        # 展示当前卡片缺失的mod信息
        self.btn_show_miss_mod = QPushButton('卡片缺失mod信息')
        self.btn_show_miss_mod.clicked.connect(self.show_current_card_missing_mod_info)
        self.btn_show_miss_mod.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred))
        self.btn_show_miss_mod.setMinimumWidth(120)
        button_layout2.addWidget(self.btn_show_miss_mod)
        main_layout.addLayout(button_layout2)

        # 重新解析卡片按钮
        self.btn_analyze_card = QPushButton('重新解析卡片')
        self.btn_analyze_card.clicked.connect(self.analyze_image)
        self.btn_analyze_card.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred))
        self.btn_analyze_card.setMinimumWidth(120)
        button_layout2.addWidget(self.btn_analyze_card)
        main_layout.addLayout(button_layout2)

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
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # 设置列宽自适应
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 第一列自适应
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 第二列根据内容调整

        # 添加复制功能支持
        self.setup_copy_function()

    def setup_copy_function(self):
        """设置复制功能"""
        # 添加快捷键
        copy_shortcut = QShortcut(QKeySequence.Copy, self.table_widget)
        copy_shortcut.activated.connect(self.copy_table_content)

        # 设置右键菜单
        self.table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.show_table_context_menu)

    def show_table_context_menu(self, position: QPoint):
        """显示表格右键菜单"""
        menu = QMenu(self)
        copy_action = menu.addAction("复制")
        copy_action.triggered.connect(self.copy_table_content)
        menu.exec_(self.table_widget.viewport().mapToGlobal(position))

    def copy_table_content(self):
        """复制表格选中的内容 - 精确复制选中的单元格"""
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            return

        # 如果只选中了一个单元格，直接复制该单元格内容
        if len(selected_items) == 1:
            cell_text = selected_items[0].text()
            QApplication.clipboard().setText(cell_text)
            self.logger.info("单元格内容已复制到剪贴板")
            return

        # 如果选中了多个单元格，按行列组织内容
        # 获取所有选中单元格的行列信息
        rows = sorted(set(item.row() for item in selected_items))
        cols = sorted(set(item.column() for item in selected_items))

        # 创建一个二维数组来存储内容
        max_row = max(rows)
        max_col = max(cols)

        # 初始化一个二维数组，用空字符串填充
        content_grid = [['' for _ in range(max_col + 1)] for _ in range(max_row + 1)]

        # 填充选中单元格的内容
        for item in selected_items:
            content_grid[item.row()][item.column()] = item.text()

        # 只处理有选中内容的行和列
        copied_text = ""
        for row in rows:
            row_text = []
            for col in cols:
                row_text.append(content_grid[row][col])
            copied_text += "\t".join(row_text) + "\n"

        # 复制到剪贴板
        if copied_text:
            QApplication.clipboard().setText(copied_text.strip())
            self.logger.info("内容已复制到剪贴板")

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
            QMessageBox.information(self, "success", "仓库mod数据生成完毕")
        except Exception as e:
            self.logger.info("mod仓库json生成失败：{}", e)
            QMessageBox.critical(self, "错误", "mod仓库json生成失败")

    def generate_mod_game_json(self):
        if not self.mod_game_path:
            QMessageBox.warning(self, "警告", "请先选择游戏mod路径！")
            return
        try:
            kk_core.generate_mod_json_file(self.mod_game_path,
                                           os.path.join(self.mod_game_path, self.mod_file_name))
            QMessageBox.information(self, "success", "游戏mod数据生成完毕")
        except Exception as e:
            self.logger.info("游戏mod信息json生成失败：{}", e)
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
            if self.mod_repository_data_cache is None:
                self.mod_repository_data_cache = self.load_mod_repository_json_file()
        except:
            QMessageBox.critical(self, "错误", "请先生成仓库mod信息")
            return

        try:
            if self.mod_game_data_cache is None:
                self.mod_game_data_cache = self.load_mod_game_json_file()
        except:
            QMessageBox.critical(self, "错误", "请先生成仓库mod信息")
            return

        try:
            card_mod_info = kk_core.get_card_mod_info(self.card_path)
            for mod in card_mod_info:
                if mod in self.mod_game_data_cache:
                    self.current_card_mod_map[mod] = self.mod_game_data_cache[mod]
                else:
                    self.current_card_mod_map[mod] = "当前mod在游戏中不存在"
            missing_mod_set = card_mod_info - self.mod_game_data_cache.keys()
            self.missing_mod_map = {}
            missing_mod_flag = False
            if len(missing_mod_set) == 0:
                self.logger.info("当前卡片在本游戏mod资源中无缺失")
                QMessageBox.information(self, "success", "当前卡片在本游戏mod资源中无缺失")
            else:
                for mod in missing_mod_set:
                    if mod in self.mod_repository_data_cache:
                        self.missing_mod_map[mod] = self.mod_repository_data_cache.get(mod)['mod_dir']
                    else:
                        self.missing_mod_map[mod] = "Not Found"
                        missing_mod_flag = True
                # 将结果渲染到列表中
                self.clear_table()
                for mod, mod_dir in self.missing_mod_map.items():
                    self.add_result_item(mod, mod_dir)

                if missing_mod_flag:
                    self.logger.info("仓库中存在当前卡片不存在的mod，请更新仓库mod信息")
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

                self.logger.info("配置文件加载成功")
            else:
                self.logger.info("配置文件不存在，跳过加载")

        except Exception as e:
            self.logger.info(f"读取配置文件时出错: {str(e)}")
            pass

    def cp_mod(self):
        if len(self.missing_mod_map) == 0:
            QMessageBox.warning(self, "提示", "不存在缺失mod需要复制")
            return
        unknown_mod = {}
        for mod, mod_dir in self.missing_mod_map.items():
            if "Not Found" == mod_dir:
                unknown_mod[mod] = mod_dir
            else:
                source_path = os.path.join(self.mod_repository_path, mod_dir)
                target_path = os.path.join(self.mod_game_path, mod_dir)
                self.copy_file_with_dirs(source_path, target_path)
        if len(unknown_mod) > 0:
            QMessageBox.warning(self, "提示", "存在仓库无法匹配的mod，请手动确认")

    def copy_file_with_dirs(self, source_path, target_path):
        if os.path.exists(target_path):
            self.logger.info("{} exists".format(target_path))
            return
        dest_dir = os.path.dirname(target_path)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        shutil.copy(source_path, target_path)

    def show_current_card_mod_info(self):
        if len(self.current_card_mod_map) == 0:
            QMessageBox.warning(self, "提示", "请选择卡片")
            return
        self.clear_table()
        for mod, mod_dir in self.current_card_mod_map.items():
            self.add_result_item(mod, mod_dir)

    def show_current_card_missing_mod_info(self):
        if len(self.missing_mod_map) == 0:
            QMessageBox.warning(self, "提示", "请选择卡片")
            return
        self.clear_table()
        for mod, mod_dir in self.missing_mod_map.items():
            self.add_result_item(mod, mod_dir)

    def closeEvent(self, event):
        """重写关闭事件，在程序退出前自动保存配置"""
        if os.path.exists(os.path.join(os.getcwd(), self.config_file_name)):
            return
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
