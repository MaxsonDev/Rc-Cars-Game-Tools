#include <iostream>
#include <vector>
#include <string>
#include <windows.h>
#include "utf8_to_cp1251.h"

#include "crsWrapper.h"
#include "pugixml/pugixml.hpp"


// тип данных функции
typedef int (__stdcall *crsGetStringType)(void *, int, char *Destination, int Count);
typedef int (fnFillEnumType)(int, char* String, int);
// typedef void(__stdcall *enmMplrFillMapEnumType)(int enum_obj, fnFillEnumType fnFillEnum);
typedef int (*GetMapDescriptionsType)(int mapCode, char *destMapKey, char* destMapName, char* destMapPoem1, char* destMapDesc, char* destMapPoem2);


// структуры 
struct MapDesc {
    std::string strPoem1;
    int intPoem1 = 0;
    std::string strMapDesc;
    int intMapDesc = 0;
    std::string strPoem2;
    int intPoem2 = 0;
};

struct MapData {
    int id = 0;
    std::string key;
    std::string name;
    MapDesc desc;
};

// переменные
static crsGetStringType crsGetString = NULL;
std::string root_folder_path;
int array_map_data_size = 0;
std::vector<MapData> array_ext_map_data;

static int arrmapGetMapDataById(int map_code, MapData& map_data){
    for (int i = 0; i < array_map_data_size; i++) {
        MapData curMap = array_ext_map_data[i];
        if (curMap.id == map_code) {
            map_data = curMap;
            return 1;
        }
    }
    return 0;
}

static void crsGetStringXML(std::string key, MapData map_data, char *Destination) {
    int txt_size;
    if (key == "Key") {
        txt_size = map_data.key.length() + 1;
        memcpy(Destination, map_data.key.c_str(), txt_size);
    }
    else if (key == "Name") {
        txt_size = map_data.name.length() + 1;
        memcpy(Destination, map_data.name.c_str(), txt_size);
    }
    else if (key == "Poem1") {
        if (map_data.desc.intPoem1 > 0) {
            crsGetString(0, map_data.desc.intPoem1, Destination, 256);
        }
        else {
            txt_size = map_data.desc.strPoem1.length() + 1;
            memcpy(Destination, map_data.desc.strPoem1.c_str(), txt_size);
        }
    }
    else if (key == "MapDesc") {
        if (map_data.desc.intMapDesc > 0) {
            crsGetString(0, map_data.desc.intMapDesc, Destination, 256);
        }
        else {
            txt_size = map_data.desc.strMapDesc.length() + 1;
            memcpy(Destination, map_data.desc.strMapDesc.c_str(), txt_size);
        }
    }
    else if (key == "Poem2") {
        if (map_data.desc.intPoem2 > 0) {
            crsGetString(0, map_data.desc.intPoem2, Destination, 256);
        }
        else {
            txt_size = map_data.desc.strPoem2.length() + 1;
            memcpy(Destination, map_data.desc.strPoem2.c_str(), txt_size);
        }
    }
}

static int GetMapDescriptions(int mapCode, char *destMapKey, char *destMapName, char *destMapPoem1, char *destMapDesc, char *destMapPoem2) {
    if (mapCode >= 0 && mapCode <= 9) {
        int result = 0;
        switch (mapCode) {
            case 0:
                crsGetString(0, 40050, destMapKey, 32);
                crsGetString(0, 40000, destMapName, 32);
                crsGetString(0, 40020, destMapPoem1, 256);
                crsGetString(0, 40030, destMapDesc, 256);
                crsGetString(0, 40040, destMapPoem2, 256);
                result = 1;
                break;
            case 1:
                crsGetString(0, 40051, destMapKey, 32);
                crsGetString(0, 40001, destMapName, 32);
                crsGetString(0, 40021, destMapPoem1, 256);
                crsGetString(0, 40031, destMapDesc, 256);
                crsGetString(0, 40041, destMapPoem2, 256);
                result = 1;
                break;
            case 2:
                crsGetString(0, 40052, destMapKey, 32);
                crsGetString(0, 40002, destMapName, 32);
                crsGetString(0, 40022, destMapPoem1, 256);
                crsGetString(0, 40032, destMapDesc, 256);
                crsGetString(0, 40042, destMapPoem2, 256);
                result = 1;
                break;
            case 3:
                crsGetString(0, 40053, destMapKey, 32);
                crsGetString(0, 40003, destMapName, 32);
                crsGetString(0, 40023, destMapPoem1, 256);
                crsGetString(0, 40033, destMapDesc, 256);
                crsGetString(0, 40043, destMapPoem2, 256);
                result = 1;
                break;
            case 4:
                crsGetString(0, 40054, destMapKey, 32);
                crsGetString(0, 40004, destMapName, 32);
                crsGetString(0, 40024, destMapPoem1, 256);
                crsGetString(0, 40034, destMapDesc, 256);
                crsGetString(0, 40044, destMapPoem2, 256);
                result = 1;
                break;
            case 5:
                crsGetString(0, 40055, destMapKey, 32);
                crsGetString(0, 40005, destMapName, 32);
                crsGetString(0, 40025, destMapPoem1, 256);
                crsGetString(0, 40035, destMapDesc, 256);
                crsGetString(0, 40045, destMapPoem2, 256);
                result = 1;
                break;
            case 6:
                crsGetString(0, 40056, destMapKey, 32);
                crsGetString(0, 40006, destMapName, 32);
                crsGetString(0, 40026, destMapPoem1, 256);
                crsGetString(0, 40036, destMapDesc, 256);
                crsGetString(0, 40046, destMapPoem2, 256);
                result = 1;
                break;
            case 7:
                crsGetString(0, 40057, destMapKey, 32);
                crsGetString(0, 40007, destMapName, 32);
                crsGetString(0, 40027, destMapPoem1, 256);
                crsGetString(0, 40037, destMapDesc, 256);
                crsGetString(0, 40047, destMapPoem2, 256);
                result = 1;
                break;
            case 8:
                crsGetString(0, 40058, destMapKey, 32);
                crsGetString(0, 40008, destMapName, 32);
                crsGetString(0, 40028, destMapPoem1, 256);
                crsGetString(0, 40038, destMapDesc, 256);
                crsGetString(0, 40048, destMapPoem2, 256);
                result = 1;
                break;
            case 9:
                crsGetString(0, 40059, destMapKey, 32);
                crsGetString(0, 40009, destMapName, 32);
                crsGetString(0, 40029, destMapPoem1, 256);
                crsGetString(0, 40039, destMapDesc, 256);
                crsGetString(0, 40049, destMapPoem2, 256);
                result = 1;
                break;
        }
        return result;
    } 
    else 
    {
        MapData map_data;
        int result = arrmapGetMapDataById(mapCode, map_data);
        if (result) {
            if (destMapKey) {
                crsGetStringXML("Key", map_data, destMapKey);
            }
            if (destMapName) {
                crsGetStringXML("Name", map_data, destMapName);
            }
            if (destMapPoem1) {
                crsGetStringXML("Poem1", map_data, destMapPoem1);
            }
            if (destMapDesc) {
                crsGetStringXML("MapDesc", map_data, destMapDesc);
            }
            if (destMapPoem2) {
                crsGetStringXML("Poem2", map_data, destMapPoem2);
            }
        }
        return 0;
	}
}

static void __stdcall enmMplrFillMapEnum(int enum_obj, fnFillEnumType fn_fill_enum) {
    char String[32];
    int total_map_len = 10;
    total_map_len += array_map_data_size;
    for (int map_code = 0; map_code < total_map_len; map_code++) {
        if (map_code <= 9) {
            int start_map_key_id = 40000;
            start_map_key_id += map_code;
            crsGetString(0, start_map_key_id, String, 32);
            fn_fill_enum(enum_obj, String, map_code);
        }
        else
        {
            MapData map_data;
            int result = arrmapGetMapDataById(map_code, map_data);
            if (result) {
                crsGetStringXML("Name", map_data, String);
                fn_fill_enum(enum_obj, String, map_code);
            }
        }
    }
}

static int __stdcall mplrIsMapCodeExist(int map_code) {
    int total_map_len = 10;
    total_map_len += array_map_data_size;
    if (map_code < total_map_len) {
        return 1;
    }
    return 0;
}

void* crsPipeWrapper(int fnId) {
    switch (fnId) {
        case 1:
            return reinterpret_cast<void*>(GetMapDescriptions);
        case 2:
            return reinterpret_cast<void*>(enmMplrFillMapEnum);
        case 3:
            return reinterpret_cast<int*>(mplrIsMapCodeExist);
        default:
            return nullptr;
    }
}

static void importFunctionsFromExe() {
	HMODULE hModule = GetModuleHandle(NULL);
	if (hModule == NULL) {
		MessageBoxA(NULL, "crs.dll не может импортировать модуль из exe файла. Это плохо!:(", "Info", MB_OK);
		return;
	}
	// MessageBoxA(NULL, "Модуль CRSGame20.dll найден!", "Info", MB_OK);

    char crsGetStringName[] = "_crsGetString@16";
    crsGetString = (crsGetStringType)GetProcAddress(hModule, crsGetStringName);
	if (crsGetString == NULL) {
		MessageBoxA(NULL, "Функция _crsGetString@16 не найдена в exe файле! Ошибка неизбежна..", "Info", MB_OK);
	}
}

static void initRootFolder() {
    char buffer[MAX_PATH];
    DWORD length = GetModuleFileNameA(nullptr, buffer, MAX_PATH);
    char* last_slash = strrchr(buffer, '\\');
    if (last_slash != nullptr) {
        *last_slash = '\0'; // Обрезаем путь после последнего слеша
    }
    root_folder_path = std::string(buffer);
    // MessageBoxA(NULL, root_folder_path.c_str(), "Info", MB_OK);
}

static void xmlParseMapDesc(MapData& new_map_data, pugi::xml_node xml_map_desc) {
    while (xml_map_desc) {
        std::string node_name = std::string(xml_map_desc.name());
        if (node_name == "Poem1") {
            std::string val = xml_map_desc.text().as_string();
            new_map_data.desc.strPoem1 = utf8_to_cp1251(val);
            new_map_data.desc.intPoem1 = xml_map_desc.attribute("str_id").as_int();
        }
        else if (node_name == "MapDescription") {
            std::string val = xml_map_desc.text().as_string();
            new_map_data.desc.strMapDesc = utf8_to_cp1251(val);
            new_map_data.desc.intMapDesc = xml_map_desc.attribute("str_id").as_int();
        }
        else if (node_name == "Poem2") {
            std::string val = xml_map_desc.text().as_string();
            new_map_data.desc.strPoem2 = utf8_to_cp1251(val);
            new_map_data.desc.intPoem2 = xml_map_desc.attribute("str_id").as_int();
        }
        xml_map_desc = xml_map_desc.next_sibling();
    }
}

static void xmlParseMapData(MapData& new_map_data, pugi::xml_node xml_map_data) {
    // добавляем id
    new_map_data.id = xml_map_data.attribute("id").as_int();
    pugi::xml_node xml_map_child = xml_map_data.first_child();
    while (xml_map_child) {
        std::string node_name = std::string(xml_map_child.name());
        if (node_name == "Key") {
            // добавляем ключ
            std::string val = xml_map_child.text().as_string();
            new_map_data.key = utf8_to_cp1251(val);
        }
        else if (node_name == "Name") {
            // добавляем имя
            std::string val = xml_map_child.text().as_string();
            new_map_data.name = utf8_to_cp1251(val);
        }
        else if (node_name == "Descriptions") {
            pugi::xml_node xml_map_desc = xml_map_child.first_child();
            xmlParseMapDesc(new_map_data, xml_map_desc);
        }
        xml_map_child = xml_map_child.next_sibling();
    }
}

static void initArrayExtMapData() {
    int map_start_id = 10;
    
    std::string file_path = root_folder_path + "\\ExtendData\\extendMapList.xml";
    pugi::xml_document xml_doc;
    if (!xml_doc.load_file(file_path.c_str())) {
        MessageBoxA(NULL, "extendMapList.xml не найден! Карты не будут загружены!", "Info", MB_OK);
    }
    
    pugi::xml_node map_list = xml_doc.child("MapList");
    array_map_data_size = std::distance(map_list.begin(), map_list.end());
    array_ext_map_data.reserve(array_map_data_size);
    
    pugi::xml_node xml_map_data = map_list.first_child();
    while (xml_map_data) {
        MapData new_map_data;
        xmlParseMapData(new_map_data, xml_map_data);
        array_ext_map_data.push_back(new_map_data);
        xml_map_data = xml_map_data.next_sibling();
    }
    // std::string str = "Количество карт " + std::to_string(array_map_data_size);
    // MessageBoxA(NULL, str.c_str(), "Info", MB_OK);
}

void crsInitDll() {
	// MessageBoxA(NULL, "Rc Cars is succefully load crs.dll! This is good!=)", "Info", MB_OK);
    importFunctionsFromExe();
    initRootFolder();
    initArrayExtMapData();
    MessageBoxA(NULL, "Модифицированная версия Недетских гонок! Приятной игры!", "Info", MB_OK);
}
