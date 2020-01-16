#!/usr/bin/python3

import requests
import re
from bs4 import BeautifulSoup

class GithubVersionManager:
   """ 
      This Class retrieve version on Github

      Releases page should be well formed
   """

   DEFAULT_GITHUB_URL = "https://github.com/"
   RELEASES_URL = "releases"
   PATTERN_VERSION = "([a-zA-Z])*(([0-9](\.)?)+((-rc[0-9]*)|(-alpha[0-9]*)|(-beta[0-9]*))?)"
   PATTERN_LAST_CHAR = ".*([0-9]$)"
   NEXT_PAGE = "?after="
   NOT_STABLE_INDICATOR = ["alpha", "beta", "rc"]

   def __init__(self, repository_owner, project, url=DEFAULT_GITHUB_URL):
      """
         Constructor: initialize variables
         :param repository_owner: the owner of the repository
         :param project: the project managed by the owner
         :param url: based URL for the repository Github by default
         :type repository_owner: String
         :type project: String
         :type url: String
         :return: None

      """
      self.repository_owner = repository_owner
      self.project = project
      self.url = url
      self.versions = []
      self.sorted = False
      self.version_prefix = None


   def get_versions(self):
      """
         Get all versions from URL and sort the tab

         :return: Tab of versions for this application
      """
      while True:
         url = f"{self.url}{self.repository_owner}/{self.project}/{self.RELEASES_URL}"
         if len(self.versions) > 0:
            if self.version_prefix is not None:
               url = f"{url}{self.NEXT_PAGE}{self.version_prefix}{self.versions[-1]}"
            else:
               url = f"{url}{self.NEXT_PAGE}{self.versions[-1]}"
         pageContent = self._get_page(url)
         if pageContent == None:
            print("It sould be there is an error. Content URL is invalid")
            exit("1")
         versions = self._get_version_from_page(pageContent)
         if len(versions) > 0:
            self.versions.extend(versions)
         else:
            break
      self._sort_versions()


   def _get_page(self, url):
      """
         Retrieve page content from its URL
         :param url: URL to parse
         :type url: String
         :return: Page content

      """
      req = requests.get(url)
      if req.status_code != 200:
         return None
      else:
         return req.text

   def _get_version_from_page(self, page_content):
      """
         Retrieve all versions inclunding in a page content
 
         :param page_content: The content to parse
         :type page_content: String
         :return: tab of versions in the page
      """
      current_versions = []
      soup = BeautifulSoup(page_content, "lxml")
      versions_in_page = soup.find_all('span', attrs={"class":"css-truncate-target"})
      if not self._is_more_page(versions_in_page):
         return current_versions
      pattern = re.compile(self.PATTERN_VERSION)
      for version_in_page in versions_in_page:
         version = pattern.search(version_in_page.string).group(2)
         if len(current_versions) > 0 :
            if version != current_versions[-1]:
               current_versions.append(version)
         else:
            current_versions.append(version)
      """ Find last version prefix """
      version_prefix = pattern.search(versions_in_page[-1].string).group(1)
      if version_prefix is not None:
         if version_prefix.lower() != version_prefix.upper():
            self.version_prefix = version_prefix
      else:
         self.version_prefix = None
      return current_versions
      
   def _is_more_page(self, versions):
      """
         Detects if webpage contains some versions infos

         :param versions: tab of versions parse in the current page
         :type url: list of String
         :return: Boolean
      """
      if versions is not None:
         if len(versions) > 0:
            return True
      return False

   def _is_version_lower(self, version_ref, version_to_compare):
      """
         Defines if a version is lower to another

         :param version_ref: Version of reference to compare
         :param version_to_compare: version to which the reference is to be compared
         :type version_ref: String
         :type version_to_compare: String
         :return: Boolean
      """
      version1 = version_ref.split(".")
      version2 = version_to_compare.split(".")
      rc1 = None
      rc2 = None

      last_version1 = version1.pop()
      v1, indicator_order_1, indicator_version_1 = self._get_lastNumber_and_rc(last_version1)
      version1.append(v1)


      last_version2 = version2.pop()
      v2, indicator_order_2, indicator_version_2 = self._get_lastNumber_and_rc(last_version2)
      version2.append(v2)
      for x, y in zip(version1, version2):
         x = int(x)
         y = int(y)
         if x < y:
            return True
         elif x != y:
            return False

      if len(version2) > len(version1):
         return True
      
      if indicator_order_1 is not None:
         if indicator_order_2 is None:
            return True
         else:
            return indicator_order_1 < indicator_order_2
      if indicator_version_1 != None and indicator_version_2 == None:
         return True
      if indicator_version_1 != None and indicator_version_2 != None:
         if indicator_version_1 < indicator_version_2:
            return True
      return False

   def _get_lastNumber_and_rc(self, number):

      """
         Defines the last number of the version and if it's an alpha, beta or rc version
         It's return the last digit of the version, the modifier and its version

         :param number: The last part of the version
         :param  number: String
         :return: String, String, String
      """
      for indicator in self.NOT_STABLE_INDICATOR:
         if f"-{indicator}" in number.lower():
            last_version_number, indicator_version = number.lower().split(f"-{indicator}")
            indicator_order = self.NOT_STABLE_INDICATOR.index(indicator)
            return last_version_number, indicator_order, indicator_version
         elif indicator in number.lower():
            last_version_number, indicator_version = number.lower().split(indicator)
            indicator_order = self.NOT_STABLE_INDICATOR.index(indicator)
            return last_version_number, indicator_order, indicator_version
      return number, None, None

   def _sort_versions(self):
      """
         Sorts the tab version from hightest to lower

         :retrun: None
      """
      while True:
         sorted = True
         for i in range(len(self.versions)-1):
            if self._is_version_lower(self.versions[i], self.versions[i+1]):
               temp = self.versions[i+1]
               self.versions[i+1] = self.versions[i]
               self.versions[i] = temp
               sorted = False
         if sorted == True:
            self.sorted = True
            return
   
   def get_lastest_version(self, only_stable = True):
      """
         Retrieves the latest version of the project

         :param not_rc: if True, return the lastest stable version
         :type not_rc: boolean

         :return: String
      """
      if self.sorted != True:
         self._sort_versions()
      for version in self.versions:
         if only_stable == True:
            for early_indicator in self.NOT_STABLE_INDICATOR:
               if early_indicator in version.lower():
                  break
            return version
         else:
            return version

   def get_last_major_version(self, major_version, only_stable = True):
      """
         Retrieves the lastest version of a specified major version

         :param major_version: The major version we wish to return
         :param only_stable: Indicates whether we are only interested in stable releases
         :type major_version: String
         :type major_version: String
         :return: String
      """
      if self.sorted != True:
         self._sort_versions()
      for version in self.versions:
         if version.startswith(major_version):
            if only_stable == True:
               for early_indicator in self.NOT_STABLE_INDICATOR:
                  if early_indicator not in version.lower():
                     break
               return version
            else:
               return version

