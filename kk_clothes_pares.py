from logger_handler import get_logger

import re
from typing import Self

# ========== 固定配置（你的规则） ==========
SIGNATURE = b'\x89PNG\r\n\x1a\n'
IEND_TYPE = b'IEND'
CHECK_KEY = b"KoiKatuClothes"
SKIP_AFTER_IEND = 8  # 固定跳过8字节
SKIP_AFTER_CHECK = 10  # 检测成功后再跳过10字节
NAME_END_BYTES = b"\x28\x00\x00\xDF\x12\x00\x00"  # 卡片名结束标志
STOP_TAG = b"<additionalAccessories"


class KKClothData:
    def __init__(self):
        self.logger = get_logger()
        self.has_clothes_card = False
        self.clothes_card_name = ""
        self.card_mod_set = set()

    def __str__(self):
        return f"CLOTHES(has_clothes_card:{self.has_clothes_card}, clothes_card_name:{self.clothes_card_name}, card_mod_set:{self.card_mod_set})"

    @classmethod
    def pares_cloth_card(cls, file_path) -> Self:
        kc = cls()
        with open(file_path, 'rb') as f:
            if f.read(8) != SIGNATURE:
                return kc

            # 遍历块直到 IEND
            while True:
                lb = f.read(4)
                if len(lb) < 4: break
                cl = int.from_bytes(lb, "big")
                ct = f.read(4)
                f.read(cl)
                f.read(4)
                if ct == IEND_TYPE:
                    extra = f.read()  # 这就是你要的原始二进制！

        if not extra:
            return kc

        ptr = 0
        # ========== 2. 跳过固定8字节 ==========
        ptr += SKIP_AFTER_IEND
        if ptr + len(CHECK_KEY) > len(extra):
            return kc

        # ========== 3. 检查是否为 KoiKatuClothes ==========
        if extra[ptr:ptr + len(CHECK_KEY)] == CHECK_KEY:
            kc.has_clothes_card = True
        else:
            return kc

        # ========== 4. 再跳过10字节 ==========
        ptr += len(CHECK_KEY) + SKIP_AFTER_CHECK

        # ========== 5. 读取卡片名：直到 NAME_END_BYTES 前一位 ==========
        end_pos = extra.find(NAME_END_BYTES, ptr)
        if end_pos == -1:
            return kc

        name_start = ptr
        name_end = end_pos - 1  # 结束标志往前一位
        card_name_bytes = extra[name_start:name_end]
        try:
            card_name = card_name_bytes.decode("utf-8", errors="ignore").strip()
            kc.clothes_card_name = card_name
        except Exception as e:
            self.logger.error("服装卡解析失败: %s", e)
            kc.clothes_card_name = f"二进制:{card_name_bytes.hex()}"

        ptr = end_pos  # 指针跳到结束标志后

        # ========== 6. 查找 KKEx → info ==========
        kkex_pos = extra.find(b"KKEx", ptr)
        if kkex_pos == -1:
            return kc

        info_pos = extra.find(b"info", kkex_pos)
        if info_pos == -1:
            return kc

        # ========== 7. 提取 ModID.xxx.Slot 直到 STOP_TAG ==========
        stop_pos = extra.find(STOP_TAG, info_pos)
        if stop_pos == -1:
            data_block = extra[info_pos:]
        else:
            data_block = extra[info_pos:stop_pos]

        # 正则提取 ModID.(.*).Slot
        pattern = re.compile(b"ModID.(.*?).Slot")
        matches = pattern.findall(data_block)
        mod_ids = [m.decode("utf-8", errors="ignore") for m in matches]
        kc.card_mod_set = set(mod_ids)

        return kc
