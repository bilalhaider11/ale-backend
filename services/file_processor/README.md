# File Processor Service
This service processes files after picking up messages from SQS.

## Development
Poetry is used for dependency management for python packages.
1. To add new package, goto [jackson_lewis_integration](./) folder and run

    ```
   poetry add PACKAGE_NAME
    ```

2. Increase the app version using
    ```
    poetry version patch | minor | major 
   ```
   **Note:** Use `patch` for patch version increase, `minor` for minor version increase or `major` for major version increase.


3. Update all dependencies using
    ```
   poetry update
   ```
   Update specific libraries using
    ```
   poetry update libraryName1 libraryName2
   ```

