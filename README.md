## Testful
A RESTful testing framework.

### Command Line Usages
Run the `testful.py` file with `--help` flag to see help messages.

### Test Structure
```json
{
	"name": "Name of the test",
	"host": "Root URL of the request server",
	"path": "Path to the request url",
	"identifier": "Macro query identifier",
	"setup": { /* Test Structure */ },
	"get": { /* Key/Value request body */ },
	"post": { /* POST request JSON body */ },
	"expected_json": { /* Expected JSON response */ },
	"teardown": { /* Test Structure */ },
	"tests": [
		/* List of Test Structures */
	]
}
```

All fields are optional and will be processed with macros.

### Testing Sequence
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
There are 2 types of macros...

#### Input Macro
Format: `<%Identifier%>` or `<%Identifier:Modifier%>`

Input macro will ask for the input data and replace the macro with it.

By default, macro will look up from the input map file for the missing key if the value is not found, user input will be asked instead. After receiving the value (from any source), the macro is set and will be reuse for the whole procedure.

Macros is a file global variable and cannot be accessed across the different files.

##### Special Macros
- `datetime:<Format>`  
Returns the formatted date time specified by format modifier.

#### Response Data Macro
Format: `<<Query>>` or `<<Identifier.Query>>`

Response data macro will be gathered from the parent's response using the query and replace the macro with the data from it.

Any field can get the grandparent's (or greater) response  using their identifier follows by the query.

Query is the list of keys joined by a dot character (`.`) which specified the path to search for the desired data.

**Example:**

```json
{
	"users": [
		{
			"name": "Alex",
			"age": 25
		}
	]
}
```

The Alex's age can be accessed using `users.0.age` query.