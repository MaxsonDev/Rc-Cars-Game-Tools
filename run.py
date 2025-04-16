from rccars_sb_file_parser import SBFileParser

if __name__ == "__main__":
    # Add Path
    file_path = ""
    sb_parser = SBFileParser(file_path)
    sb_parser.parse_file()
    DESC = sb_parser.get_desc_data_result()
    print("VELL DONE!")