#!/usr/bin/python
# coding:utf-8
"""
Instagram Downloader
"""

import os
import logging
import time
import requests
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup as bs

class MyApp(object):
    """
    define the GUI interface
    """
    def __init__(self):
        self.set_log()
        self.root = tk.Tk()
        self.root.title("Instgram Downloader")
        self.root.geometry('500x250')
        self.canvas = tk.Canvas(self.root, height=400, width=700)
        self.canvas.pack(side='top')
        self.setup_ui()

    def set_log(self):
        if not os.path.exists('./screenshot'):
            os.mkdir('./screenshot')
        if not os.path.exists('./log'):
            os.mkdir('./log')
        log_name = 'log/RPA_%Y%m%d_%H%M%S.log'
        logging.basicConfig(level=logging.INFO,
                            filename=datetime.now().strftime(log_name),
                            filemode='w',
                            format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
        self.logger = logging.getLogger(log_name)

    def setup_ui(self):
        """
        setup UI interface
        """
        self.label_save_file = tk.Label(self.root, text='存檔資料夾:')
        self.label_pattern = tk.Label(self.root, text = "選擇模式：")
        self.label_id = tk.Label(self.root, text = "id or tag：")
        self.label_limit = tk.Label(self.root, text='圖片上限:')
        
        self.input_save_file = tk.Entry(self.root, width=30)
        self.input_pattern = ttk.Combobox(self.root, values=["id", "tag"])
        self.input_pattern.current(0)
        self.input_limit = tk.Entry(self.root, width=30)
        self.input_id = tk.Entry(self.root, width=30)
        self.input_tag = tk.Entry(self.root, width=30)
        self.login_button = tk.Button(self.root, command=self.run, text="Run", width=10, foreground = "black")
        self.quit_button = tk.Button(self.root, command=self.quit, text="Quit", width=10, foreground = "black")

    def gui_arrang(self):
        """
        setup position of UI
        """
        self.label_save_file.place(x=60, y=30)
        self.label_pattern.place(x=60, y=70)
        self.label_id.place(x=60, y=110)
        self.label_limit.place(x=60, y=150)
        
        self.input_save_file.place(x=130, y=30)
        self.input_pattern.place(x=130, y=70)
        self.input_id.place(x=130, y=110)
        self.input_limit.place(x=130, y=150)
        
        self.login_button.place(x=130, y=190)
        self.quit_button.place(x=270, y=190)

    def check(self):
        """
        check the input of gui interface
        return:
            True
            False
        """
        # check your input
        self.save_file = self.input_save_file.get()
        self.pattern = self.input_pattern.get()
        self.id = self.input_id.get()
        
        if len(self.save_file) == 0 or len(self.pattern) == 0 or \
           len(self.id)==0 or len(self.input_limit.get())==0:
            messagebox.showinfo(title='System Alert', message='不得為空！')
            self.logger.info('填選處為空值！')
            return False
        
        try:
            self.limit = int(self.input_limit.get())
        except:
            messagebox.showinfo(title='System Alert', message='限制數應為整數！')
            self.logger.info('限制數應為整數！')
            return False
        
         # check your save file
        if not self.pattern in ['id','tag']:
            messagebox.showinfo(title='System Alert', message=f'模式輸入有誤')
            self.logger.warning('The pattern is wrong!')
            return False
        
        # check your save file
        if self.save_file in ['log','screenshot']:
            messagebox.showinfo(title='System Alert', message=f'該資料夾檔名不可使用！')
            self.logger.warning('The file name is wrong!')
            return False
        
        if not os.path.exists(f'./{self.save_file}'):
            os.mkdir(f'./{self.save_file}')
            messagebox.showinfo(title='System Alert', message=f'已建立{self.save_file}的資料夾')
            self.logger.info(f'Make dir:{self.save_file}')
            
        return True


    def download(self):
        """
        download instagram photo
        """
        # get driver
        driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.maximize_window()
        
        # create url
        if self.pattern=='id':
            user_id = self.id
        elif self.pattern=='tag':
            user_id = f'explore/tags/{self.id}/'
        origin_url = 'https://www.instagram.com/' + user_id
        
        driver.get(origin_url)

        time.sleep(3)
        SCROLL_PAUSE_TIME = 3
        images_unique=[]
        # Get scroll height
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait
            time.sleep(1)

            # show more if exists
            try:
                button_name = f'顯示更多 {user_id} 的貼文'
                show_more = driver.find_element_by_xpath(f"//*[contains(text(),'{button_name}')]")
                show_more.click()
            except:
                pass

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                driver.execute_script("window.scrollTo(document.body.scrollHeight,0);")
                break

            # This means that there is still photos to scrap
            last_height = new_height
            time.sleep(1)

            # Retrive the html
            html_to_parse = str(driver.page_source)
            html = bs(html_to_parse,"html5lib")

            # Get the image's url
            images_url = html.findAll("img", {"class": "FFVAD"})

            # Check if they are unique
            in_first = set(images_unique)
            in_second = set(images_url)

            in_second_but_not_in_first = in_second - in_first

            result = images_unique + list(in_second_but_not_in_first)
            images_unique = result

            # if the images greater than the limit, break
            if len(images_unique)>self.limit:
                break

        num_images = len(images_unique)
        self.logger.info(f'抓到{num_images}張圖片')
        
        #Close the webdriver 
        driver.close()

        for i, _ in enumerate(images_unique):
            try:
                # Save each image.jpg file
                name=f"./{self.save_file}/{self.id}"+str(i)+".jpg"
                with open(name, 'wb') as handler:
                    img_data = requests.get(images_unique[i].get("src")).content
                    handler.write(img_data)
            except:
                self.logger.warning('無法存取:{}'.format(images_unique[i]))
            
    def run(self):
        """
        when you click the button of run, it'll execute
        """
        start_time = datetime.now()

        if self.check():
            self.download()
            messagebox.showinfo(title='System Alert', message='程式執行完畢！')
        else:
            self.logger.warning('檢查不通過！')

        end_time = datetime.now()
        execution_time = (end_time-start_time).seconds
        self.logger.info('Total Execution time:', execution_time, 's')
        messagebox.showinfo(title='System Alert', message=f'執行時間:{execution_time}秒')

    def quit(self):
        """
        when you click the button of quit, it'll execute
        """
        self.root.destroy()

def main():
    """
    main function for MyApp
    """
    # initial
    app = MyApp()
    # arrage gui
    app.gui_arrang()
    # run tkinter
    tk.mainloop()


if __name__ == '__main__':
    main()