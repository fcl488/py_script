import json
import os
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from kkloader import KoikatuCharaData
import logging

logging.basicConfig(level=logging.INFO)

MOD_REPOSITORY_JSON_PATH = "D:\\kk_mod.json"
MOD_REPOSITORY_PATH = "D:\\ForCharactersLoading"
GAME_MOD_JSON_PATH = "D:\\ForCharactersLoading\\kk_mod.json"
GAME_MOD_PATH = "D:\\ForCharactersLoading"
GAME_CARD_PATH = "D:\\BaiduNetdiskDownload\\Rat_Koikatu_F_20250714223150741_Yixuan.png"


def get_zip_mod_guid(mod_dir):
    try:
        with zipfile.ZipFile(mod_dir, 'r') as zip_ref:
            # 获取所有文件列表
            file_list = zip_ref.namelist()

            # 查找 ZIP 中的 XML 文件（假设只有一个）
            xml_files = [f for f in file_list if f.lower().endswith('.xml')]

            if not xml_files:
                print("ZIP 文件中没有 XML 文件")
                return None
            else:
                # 读取第一个 XML 文件
                xml_file = xml_files[0]
                with zip_ref.open(xml_file) as file:
                    xml_content = file.read().decode('utf-8')  # 如果是二进制 XML，可去掉 decode()
                    # print(xml_content)
                    root = ET.fromstring(xml_content)
                    result = {elem.tag: elem.text or None for elem in root}
                    result['schema-ver'] = root.attrib['schema-ver']  # 添加属性
                    # print(result)
                    return result
    except Exception as e:
        print(e)
        return None


# 生成mod的guid和mod路径映射json
def generate_mod_json_file(mod_path, mod_json_path):
    kk_mod_map = {}
    for zipmod_path in Path(mod_path).glob('**/*.zipmod'):
        zip_mod_data_map = get_zip_mod_guid(zipmod_path)
        logging.info(zip_mod_data_map)
        if zip_mod_data_map:
            kk_mod_map[zip_mod_data_map['guid']] = {'name': zip_mod_data_map['name'],
                                                    'mod_dir': get_relative_path(zipmod_path, mod_path)}
    with open(mod_json_path, "w", encoding="utf-8") as f:
        json.dump(kk_mod_map, f, indent=4, ensure_ascii=False)  # ensure_ascii=False 支持中文


# 仓库生成mod的guid和mod路径映射json
def generate_mod_json_file_repository():
    generate_mod_json_file(MOD_REPOSITORY_PATH, MOD_REPOSITORY_JSON_PATH)


# 游戏生成mod的guid和mod路径映射json
def generate_mod_json_file_game():
    generate_mod_json_file(GAME_MOD_PATH, GAME_MOD_JSON_PATH)


# 去掉根路径
def get_relative_path(full_path, root_path):
    try:
        return str(Path(full_path).relative_to(Path(root_path)))
    except ValueError:
        return full_path  # 或者返回原路径


def get_card_mod_info(card_path):
    kc = KoikatuCharaData.load(card_path)
    start = 8
    mod_set = set()
    # /xa4 结尾
    # print(kc['KKEx']['data']['com.bepis.sideloader.universalautoresolver'][1]['info'])
    # print(kc['KKEx']['com.bepis.sideloader.universalautoresolver'][1]['info'])
    # print(type(kc['KKEx']['com.bepis.sideloader.universalautoresolver'][1]['info'][0]))
    for info in kc['KKEx']['com.bepis.sideloader.universalautoresolver'][1]['info']:
        end = info.find(b'\xa4', start)
        # print(info[start:end].decode('utf-8'))
        mod_set.add(info[start:end].decode('utf-8'))
    return mod_set


def save_card_mod_info(card_mod_info_dir, base_path, file_name):
    with open(os.path.join(base_path, file_name), 'w', encoding='utf-8') as f:
        json.dump(card_mod_info_dir, f, ensure_ascii=False, indent=4)


'''
1. mod 仓库json文件
2. 更新mod仓库json文件
3. 获取卡片mod信息
4. 获取当前游戏mod信息
5. 更新当前游戏mod的json文件
6. 将卡片mod信息与当前游戏mod信息进行比较 获取到当前游戏不存在的mod 然后去总仓库寻找不存在的mod信息 有不存在mod信息的给出json文件 都存在则提示都存在
'''


# 加载仓库的mod json数据
def load_mod_repository_json_file():
    if not os.path.exists(MOD_REPOSITORY_JSON_PATH):
        generate_mod_json_file_repository()
    try:
        with open(MOD_REPOSITORY_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return None


# 获取游戏的mod json数据
def load_mod_game_json_file():
    if not os.path.exists(GAME_MOD_JSON_PATH):
        generate_mod_json_file_game()
    try:
        with open(GAME_MOD_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return None


# 保存缺失的mod的数据 位置在当前脚本目录下
def save_missing_mod_info_json_file(missing_mod_map):
    file_name = os.path.splitext(os.path.basename(GAME_CARD_PATH))[0] + ".missing.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(missing_mod_map, f, ensure_ascii=False, indent=4)


def analysis_card():
    # 获取仓库mod信息
    repository_mod_json = load_mod_repository_json_file()
    if repository_mod_json is None:
        logging.info("无仓库mod的json文件，请先生成仓库mod的json文件")
        return
    # 获取游戏mod信息
    game_mod_json = load_mod_game_json_file()
    if game_mod_json is None:
        logging.info("无游戏mod的json文件，请先生成游戏mod的json文件")
        return
    # 获取卡片mod信息
    card_mod_info = get_card_mod_info(GAME_CARD_PATH)
    missing_mod_set = card_mod_info - game_mod_json.keys()
    missing_mod_map = {}
    missing_mod_flag = False
    if len(missing_mod_set) == 0:
        logging.info("当前卡片在本游戏mod资源中无缺失")
    else:
        for mod in missing_mod_set:
            if mod in repository_mod_json:
                missing_mod_map[mod] = repository_mod_json.get(mod)['mod_dir']
            else:
                missing_mod_map[mod] = "Not Found"
                missing_mod_flag = True
        save_missing_mod_info_json_file(missing_mod_map)
        if missing_mod_flag:
            logging.info("仓库中存在当前卡片不存在的mod，请更新仓库mod信息")


if __name__ == '__main__':
    generate_mod_json_file_repository()
    generate_mod_json_file_game()
    analysis_card()
