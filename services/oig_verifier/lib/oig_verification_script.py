#!/usr/bin/env python3
"""
OIG Automated Verification Script
v1.0.0

This script automates the verification process on the OIG exclusions website.
It searches for a person by name and then verifies their SSN.
"""

import argparse
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OIGVerifier:
    def __init__(self, screenshot_dir="screenshots"):
        """
        Initialize the OIG Verifier
        
        Args:
            screenshot_dir (str): Directory to save screenshots
        """
        self.base_url = "https://exclusions.oig.hhs.gov/Default.aspx"
        self.screenshot_dir = screenshot_dir
        self.driver = None
        self.current_result_dir = None
        self.screenshot_index = 0
        
        # Create main screenshot directory if it doesn't exist
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Check if running in Docker environment
        selenium_host = os.environ.get('SELENIUM_HOST', 'selenium')
        selenium_port = os.environ.get('SELENIUM_PORT', '4444')
        
        if selenium_host != 'localhost':
            # Running in Docker - use Remote WebDriver
            try:
                selenium_url = f"http://{selenium_host}:{selenium_port}/wd/hub"
                logger.info(f"Connecting to Selenium Grid at: {selenium_url}")
                
                self.driver = webdriver.Remote(
                    command_executor=selenium_url,
                    options=chrome_options
                )
                self.driver.implicitly_wait(10)
                
                logger.info("Remote Chrome WebDriver initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Remote Chrome WebDriver: {e}")
                raise Exception(f"Remote Chrome WebDriver initialization failed. Error: {e}")
        else:
          logger.error(f"Can't run OIG verification script on local")
          raise Exception(f"Can't run OIG verification script on local")
    
    def take_screenshot(self, filename):
        """Take a screenshot and save it to the current result directory"""
        if not self.current_result_dir:
            logger.error("No result directory set")
            return None
        
        # Increment screenshot index
        self.screenshot_index += 1
        
        # Create filename with index prefix
        indexed_filename = f"{self.screenshot_index:02d}_{filename}.png"
        full_filename = f"{self.current_result_dir}/{indexed_filename}"
        
        try:
            self.driver.save_screenshot(full_filename)
            logger.info(f"Screenshot saved: {full_filename}")
            return full_filename
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None
    
    def search_by_name(self, first_name, last_name):
        """
        Search for a person by name on the OIG website
        
        Args:
            first_name (str): First name
            last_name (str): Last name
            
        Returns:
            bool: True if search results found, False otherwise
        """
        try:
            logger.info(f"Searching for: {first_name} {last_name}")
            
            # Navigate to the main page
            self.driver.get(self.base_url)
            time.sleep(3)  # Simple wait for page load
            
            # Fill in the first name
            first_name_field = self.driver.find_element(By.ID, "ctl00_cpExclusions_txtSPFirstName")
            first_name_field.clear()
            first_name_field.send_keys(first_name)
            
            # Fill in the last name
            last_name_field = self.driver.find_element(By.ID, "ctl00_cpExclusions_txtSPLastName")
            last_name_field.clear()
            last_name_field.send_keys(last_name)
            
            self.take_screenshot("before_search")
            
            # Click the Search button
            search_button = self.driver.find_element(By.ID, "ctl00_cpExclusions_ibSearchSP")
            search_button.click()
            
            # Wait for results page to load
            time.sleep(5)
            self.take_screenshot("search_results")
            
            # Check if we have search results by looking for the results table
            try:
                results_table = self.driver.find_element(By.ID, "ctl00_cpExclusions_gvEmployees")
                logger.info("Search results found")
                return True
            except NoSuchElementException:
                logger.info("No search results found")
                return False
                    
        except Exception as e:
            logger.error(f"Error during name search: {e}")
            self.take_screenshot("search_error")
            return False
    
    def verify_ssn(self, ssn):
        """
        Verify SSN for the first result found
        
        Args:
            ssn (str): SSN without dashes
            
        Returns:
            str: "Match" or "No Match" or "Error"
        """
        try:
            logger.info(f"Verifying SSN: {ssn}")
            
            # Find the first "Verify" link
            verify_links = self.driver.find_elements(By.XPATH, "//a[contains(@id, 'cmdVerify')]")
            
            if not verify_links:
                logger.warning("No Verify links found")
                return "Error: No Verify links found"
            
            # Click the first Verify link
            verify_links[0].click()
            time.sleep(3)
            self.take_screenshot("verify_page")
            
            # Enter the SSN
            ssn_field = self.driver.find_element(By.ID, "ctl00_cpExclusions_txtSSN")
            ssn_field.clear()
            ssn_field.send_keys(ssn)
            
            self.take_screenshot("before_verify")
            
            # Click the Verify button
            verify_button = self.driver.find_element(By.ID, "ctl00_cpExclusions_ibtnVerify")
            verify_button.click()
            
            # Wait for verification result
            time.sleep(3)
            self.take_screenshot("verification_result")
            
            # Check the result based on the actual HTML structure
            try:
                # Look for the "NO MATCH" popup
                no_match_popup = self.driver.find_element(By.ID, "ctl00_cpExclusions_invalid")
                if no_match_popup.is_displayed():
                    logger.info("SSN verification failed - No match found")
                    return "No Match"
            except NoSuchElementException:
                pass
            
            # Look for the no-match image
            try:
                no_match_img = self.driver.find_element(By.ID, "ctl00_cpExclusions_print_verification")
                if "verify-no-match" in no_match_img.get_attribute("src"):
                    logger.info("SSN verification failed - No match found (image)")
                    return "No Match"
            except NoSuchElementException:
                pass
            
            # Look for the match image
            try:
                match_img = self.driver.find_element(By.ID, "ctl00_cpExclusions_print_verification")
                if "verify-match" in match_img.get_attribute("src") or "verify-identity" in match_img.get_attribute("src"):
                    logger.info("SSN verification successful - Match found (image)")
                    return "Match"
            except NoSuchElementException:
                pass
            
            # If we can't determine the result clearly, check if we're still on the verify page
            try:
                self.driver.find_element(By.ID, "ctl00_cpExclusions_txtSSN")
                logger.warning("Still on verify page - could not determine result, assuming No Match")
                return "No Match"
            except NoSuchElementException:
                pass
            
            # If we can't determine the result, assume No Match for safety
            logger.warning("Could not determine verification result, assuming No Match")
            return "No Match"
                        
        except Exception as e:
            logger.error(f"Error during SSN verification: {e}")
            self.take_screenshot("verification_error")
            return f"Error: {str(e)}"
    
    def verify_person(self, first_name, last_name, ssn):
        """
        Complete verification process for a person
        
        Args:
            first_name (str): First name
            last_name (str): Last name
            ssn (str): SSN without dashes
            
        Returns:
            str: "Match", "No Match", or error message
        """
        try:
            # Create initial directory for screenshots
            timestamp = time.strftime("%Y_%m_%d_%H_%M_%S_%Z")
            temp_dir_name = f"{first_name}_{last_name}_{ssn}_temp_{timestamp}"
            self.current_result_dir = os.path.join(self.screenshot_dir, temp_dir_name)
            
            # Create the initial directory
            os.makedirs(self.current_result_dir, exist_ok=True)
            logger.info(f"Created temporary directory: {self.current_result_dir}")
            
            # Reset screenshot index for new verification
            self.screenshot_index = 0
            
            # Step 1: Search by name
            search_success = self.search_by_name(first_name, last_name)
            
            if not search_success:
                # Rename directory for no match
                result = "NoMatch"
                final_dir_name = f"{first_name}_{last_name}_{ssn}_{result}_{timestamp}"
                final_dir = os.path.join(self.screenshot_dir, final_dir_name)
                os.rename(self.current_result_dir, final_dir)
                self.current_result_dir = final_dir
                logger.info(f"Renamed directory to: {self.current_result_dir}")
                return "No Match: No search results found"
            
            # Step 2: Verify SSN
            result = self.verify_ssn(ssn)
            
            # Rename directory based on verification result
            if "No Match" in result:
                result_word = "NoMatch"
            elif "Match" in result:
                result_word = "Match"
            else:
                result_word = "Error"
            
            final_dir_name = f"{first_name}_{last_name}_{ssn}_{result_word}_{timestamp}"
            final_dir = os.path.join(self.screenshot_dir, final_dir_name)
            os.rename(self.current_result_dir, final_dir)
            self.current_result_dir = final_dir
            logger.info(f"Renamed directory to: {self.current_result_dir}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in verification process: {e}")
            return f"Error: {str(e)}"
    
    def close(self):
        """Close the browser and clean up"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")