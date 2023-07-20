import sys
import configparser

assert len(sys.argv) == 2
filename = sys.argv[1]


        

def copy_ini_section(source_file, destination_file, source_section, destination_section):
    # Read the contents of the source INI file
    with open(source_file, 'r') as source:
        lines = source.readlines()

    # Find the start and end indices of the source section
    start_index = None
    end_index = None
    for i, line in enumerate(lines):
        if line.strip() == '[' + source_section + ']':
            start_index = i
        elif start_index is not None and line.strip().startswith('['):
            end_index = i
            break
    if end_index is None:
        end_index = len(lines)

    # Read the contents of the destination INI file
    with open(destination_file, 'r') as destination:
        destination_lines = destination.readlines()

    # Find the index where the destination section should be inserted
    insert_index = None
    for i, line in enumerate(destination_lines):
        if line.strip() == '[' + destination_section + ']':
            insert_index = i
            break
    if insert_index is None:
        insert_index = len(destination_lines)

    # Insert the source section into the destination lines
    destination_lines[insert_index:insert_index] = lines[start_index:end_index]

    # Write the updated contents to the destination INI file
    with open(destination_file, 'w') as destination:
        destination.writelines(destination_lines)


# Usage example
#copy_ini_section('source.ini', 'destination.ini', 'source_section', 'destination_section')

def get_reahl_requires(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    requires = config['options']['install_requires']
    reahl_requires = [i for i in requires.split('\n') if i.startswith('reahl-')]
    return reahl_requires

def add_to_version_history(filename, requirements):
    with open(filename, 'r') as f:
        lines = f.readlines()

    with open(filename, 'w') as f:
        for line in lines:
            f.writelines([line])
            
            if line.strip() == "[versions.'6.1']":
                f.write('  install_requires = [\n')
                f.write('    ')
                f.write(',\n    '.join([f'"{i}"' for i in requirements]))
                f.write('\n  ]\n')
                
    

requirements = get_reahl_requires(filename)
add_to_version_history(filename, requirements)

