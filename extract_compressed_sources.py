import subprocess
import os
import shutil
from logger import Log_level

def unzip_with_tar(DOWNLOAD_FOLDER, filename, EXTRACTED_FOLDER):
    # create a folder for the output
    output_folder = os.path.join(EXTRACTED_FOLDER, filename)
    os.makedirs(output_folder, exist_ok=False)
    # attempt unzip
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    completed_proc = subprocess.run(['tar', '-xf', filepath, '-C', output_folder])
    if completed_proc.returncode != 0:
        if os.path.exists(output_folder): os.removedirs(output_folder)
    return completed_proc

def unzip_with_gunzip(DOWNLOAD_FOLDER, filename, EXTRACTED_FOLDER):
    # create a folder for the output
    output_folder = os.path.join(EXTRACTED_FOLDER, filename)
    os.makedirs(output_folder, exist_ok=False)
    # copy the file to uzip
    output_filepath = os.path.join(output_folder, filename + '.gz')
    shutil.copy(os.path.join(DOWNLOAD_FOLDER, filename), output_filepath)
    # attempt unzip
    completed_proc = subprocess.run(['gunzip', output_filepath])
    if completed_proc.returncode != 0:
        if os.path.exists(output_folder): os.removedirs(output_folder)
    return completed_proc

def log_proc_result(proc, name, desc, LOGGER):
    ret = proc.returncode
    if ret == 0:
        LOGGER.log(Log_level.DEBUG, f'[{name}] success\t{desc}')
        return
    LOGGER.log(Log_level.WARN, f'[{name}] ret={ret}\t{desc}') 
    if proc.stdout: LOGGER.log(Log_level.WARN, f'\tstdout:{proc.stdout}') 
    if proc.stderr: LOGGER.log(Log_level.WARN, f'\tstderr:{proc.stderr}') 

def main(DOWNLOAD_FOLDER, EXTRACTED_FOLDER, LOGGER):
    failed_extractions = []
    success_extractions = []
    for _, _, files in os.walk(DOWNLOAD_FOLDER):
        for filename in files:
            try:
                # try tar, then gunzip
                proc_tar = unzip_with_tar(DOWNLOAD_FOLDER, filename, EXTRACTED_FOLDER)
                if proc_tar.returncode == 0: 
                    log_proc_result(proc_tar, 'tar unzip', filename, LOGGER)
                    success_extractions.append(filename)
                    continue
                proc_gunzip = unzip_with_gunzip(DOWNLOAD_FOLDER, filename, EXTRACTED_FOLDER)
                if proc_gunzip.returncode == 0: 
                    log_proc_result(proc_gunzip, 'gunzip', filename, LOGGER)
                    success_extractions.append(filename)
                    continue
                # log failed extractions
                failed_extractions.append(filename)
                LOGGER.log(Log_level.WARN, f'extraction failed for {filename}')
                log_proc_result(proc_tar, 'tar unzip', filename, LOGGER)
                log_proc_result(proc_gunzip, 'gunzip', filename, LOGGER)
            except subprocess.CalledProcessError as e:
                LOGGER.log(Log_level.ERROR, f"[extract_compressed_sources] error extracting {filename}")
                print(e)
    LOGGER.log(Log_level.INFO, f'{len(success_extractions)} files extracted. \t{len(failed_extractions)} failures.\n\tfailed:{failed_extractions}')

