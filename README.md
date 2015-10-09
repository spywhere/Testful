## Testful
A RESTful testing framework.

### Command Line Usages
Run the `testful.py` file with `--help` flag to see help messages.

### Test Configurations
By default, Testful will search the `test_config.yaml` file for test configurations which has the following format...

```yaml
# A boolean specified whether the test will be run or not
run_test: true
# A boolean specified whether the test results file will be generated or not
generate_result: false
# A string specified a path to input map file
input: path/to/InputMap.yaml
# A list consists of strings specified the path to each test structure file
tests:
- path/to/Test1.yaml
- path/to/Test2.yaml
- # ... more tests
```

### Test Structure
Test structure is simply a one big test case which has the following format...

```yaml
name: Name of the test
host: Root URL of the request server
path: Path to the request url
identifier: Macro query identifier
setup: # Test Structure
get: # Key/Value request body
post: # POST request body
expected_json: # Expected response
teardown: # Test Structure
tests:
- # Test Structure
- # Test Structure
- # ... more tests
```

All fields are optional and will be processed with macros.

### Testing Sequence
Testful will run the test in the following sequence...

1. Setup is determined
  - Run the setup sequence
  - Stop the test on failed
2. Test is determined
  - Run the test
  - Run the teardown on failed
  - Write the test results to file
3. Child tests are determined
  - Run the child tests
  - Run the teardown on failed
4. Teardown is determined
  - Run the teardown sequence
5. Returns the test result

### Macro System
Macro is a token use to identify the data placement which can be helpful on a big complicate test case.

There are 2 types of macros...

#### Input Macro
Format: `<%Identifier%>` or `<%Identifier:Modifier%>`

Input macro will ask for the input data and replace the macro with it.

By default, macro will look up from the input map file for the missing key, if the value is not found, user input will be asked instead. After receiving the value (from any source), the macro is set and will be reuse for the whole procedure.

Macros is a file global variable and cannot be accessed across the different files.

##### Special Macros
Special macro has a dynamic return value which can be changed based on current context of the test.

You can override the special macro with normal macro by simply create a macro with the same name with the special macro you want to replace.

- Date Time  
**Identifier**: `datetime`  
**Modifier**: [Python's date time format](https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior)  
Returns the formatted date time specified by format modifier.

**Example**:  
`<%datetime:%d/%m/%Y%>` will returns `09/10/2015`.

#### Response Data Macro
Format: `<<Query>>` or `<<Identifier.Query>>`

Response data will be gathered from the parent's response using the query and replace the macro with the data from it.

Any field can get the grandparent's (or greater) response  using their identifier follows by the query.

Query is the list of keys joined by a dot character (`.`) which specified the path to search for the desired data.

**Example:**

```yaml
users:
- name: Alax
  age: 25
```

The Alex's age can be accessed using `users.0.age` query.

**Example 2:**

```yaml
- name: Account Inquiry
  identifier: query
  post:
    user: Alex
  expected_json:
    accounts:
    - accountNumber: 1000
    - accountNumber: 1001
  tests:
  - name: Account Detail
    post:
      accountNumber: <<query.accounts.0.accountNumber>>
    expected_json:
      accountNumber: 1000
      accountAmount: 50
```

The query `query.accounts.0.accountNumber` will be replaced with `1000`.