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

# Import S3 client service
from common.services.s3_client import S3ClientService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OIGVerifier:
    def __init__(self):
        """
        Initialize the OIG Verifier
        """
        self.base_url = "https://exclusions.oig.hhs.gov/Default.aspx"
        self.driver = None
        
        # Initialize S3 client
        self.s3_client = S3ClientService()
        
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
    
    def take_screenshot(self, filename, organization_id, person_id):
        """Take a screenshot and save it to S3 with the specified naming convention"""
        try:
            # Create temporary local filename
            temp_local_path = f"/tmp/{filename}_{int(time.time())}.png"
            
            # Take screenshot locally first
            self.driver.save_screenshot(temp_local_path)
            logger.info(f"Temporary screenshot saved: {temp_local_path}")
            
            # Generate S3 key with the specified naming convention
            today = datetime.now().strftime("%Y-%m-%d")
            s3_key = f"{organization_id}/oig_exclusion/{person_id}/{today}.png"
            
            # Upload to S3
            self.s3_client.upload_file(
                file_path=temp_local_path,
                s3_key=s3_key,
                content_type="image/png",
                metadata={
                    "organization_id": organization_id,
                    "person_id": person_id,
                    "verification_date": today,
                    "screenshot_type": filename
                }
            )
            
            logger.info(f"Screenshot uploaded to S3: {s3_key}")
            
            # Generate presigned URL for accessing the screenshot
            presigned_url = self.s3_client.generate_presigned_url(s3_key, expiration=604800)
            logger.info(f"Generated presigned URL: {presigned_url}")
            
            # Clean up temporary local file
            try:
                os.remove(temp_local_path)
                logger.info(f"Cleaned up temporary file: {temp_local_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_local_path}: {e}")
            
            # Return both S3 key and presigned URL for flexibility
            return {
                's3_key': s3_key,
                'presigned_url': presigned_url,
                'expires_in': 604800  # 7 days in seconds
            }
            
        except Exception as e:
            logger.error(f"Failed to take and upload screenshot: {e}")
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
            
            # Click the Search button
            search_button = self.driver.find_element(By.ID, "ctl00_cpExclusions_ibSearchSP")
            search_button.click()
            
            # Wait for results page to load
            time.sleep(5)
            
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
            return False
    
    def verify_ssn(self, ssn):
        """
        Verify SSN for the first result found
        
        Args:
            ssn (str): SSN without dashes
            
        Returns:
            str: "Match", "NoMatch", or "Error"
        """
        try:
            logger.info(f"Verifying SSN: {ssn}")
            
            # Find the first "Verify" link
            verify_links = self.driver.find_elements(By.XPATH, "//a[contains(@id, 'cmdVerify')]")
            
            if not verify_links:
                logger.warning("No Verify links found")
                return "Error"
            
            # Click the first Verify link
            verify_links[0].click()
            time.sleep(3)
            
            # Enter the SSN
            ssn_field = self.driver.find_element(By.ID, "ctl00_cpExclusions_txtSSN")
            ssn_field.clear()
            ssn_field.send_keys(ssn)
            
            # Click the Verify button
            verify_button = self.driver.find_element(By.ID, "ctl00_cpExclusions_ibtnVerify")
            verify_button.click()
            
            # Wait for verification result
            time.sleep(3)
            
            # Check the result based on the actual HTML structure
            try:
                # Look for the "NO MATCH" popup
                no_match_popup = self.driver.find_element(By.ID, "ctl00_cpExclusions_invalid")
                if no_match_popup.is_displayed():
                    logger.info("SSN verification failed - No match found")
                    return "NoMatch"
            except NoSuchElementException:
                pass
            
            # Look for the no-match image
            try:
                no_match_img = self.driver.find_element(By.ID, "ctl00_cpExclusions_print_verification")
                if "verify-no-match" in no_match_img.get_attribute("src"):
                    logger.info("SSN verification failed - No match found (image)")
                    return "NoMatch"
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
                logger.warning("Still on verify page - could not determine result, assuming NoMatch")
                return "NoMatch"
            except NoSuchElementException:
                pass
            
            # If we can't determine the result, assume NoMatch for safety
            logger.warning("Could not determine verification result, assuming NoMatch")
            return "NoMatch"
                        
        except Exception as e:
            logger.error(f"Error during SSN verification: {e}")
            return "Error"
    
    def verify_person(self, first_name, last_name, ssn, organization_id, person_id):
        """
        Complete verification process for a person
        
        Args:
            first_name (str): First name
            last_name (str): Last name
            ssn (str): SSN without dashes
            organization_id (str): Organization ID for S3 upload
            person_id (str): Person ID for S3 upload
            
        Returns:
            str: "Match", "NoMatch", "NoSearch", or "Error"
        """
        try:
            # Step 1: Search by name
            search_success = self.search_by_name(first_name, last_name)
            
            if not search_success:
                # Take final screenshot for NoSearch result and upload to S3
                screenshot_result = self.take_screenshot("nosearch_result", organization_id, person_id)
                logger.info(f"No search results found. Screenshot uploaded to S3: {screenshot_result}")
                return "NoSearch"
            
            # Step 2: Verify SSN
            result = self.verify_ssn(ssn)
            
            # Take final screenshot based on result and upload to S3
            screenshot_result = None
            if result == "Match":
                screenshot_result = self.take_screenshot("match_result", organization_id, person_id)
            elif result == "NoMatch":
                screenshot_result = self.take_screenshot("nomatch_result", organization_id, person_id)
            elif result == "Error":
                screenshot_result = self.take_screenshot("error_result", organization_id, person_id)
            
            logger.info(f"Verification result: {result}. Screenshot uploaded to S3: {screenshot_result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in verification process: {e}")
            # Take error screenshot if possible
            try:
                screenshot_result = self.take_screenshot("error_result", organization_id, person_id)
                logger.info(f"Error screenshot uploaded to S3: {screenshot_result}")
            except:
                pass
            return "Error"
    
    def close(self):
        """Close the browser and clean up"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")