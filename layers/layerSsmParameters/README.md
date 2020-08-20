# AWS SSM Parameter Cache
> Provides a cache that loads AWS Systems Manager Parameter Store values and refreshes the values periodically


## Install

This library can be used either as a Lambda Layer or by copying the class file into your project. By default the Lambda Layer is defined in
`template.yml` and you only need to update the file to add a reference to the layer for your Lambda Function and create or update an IAM Role to allow access to the SSM Parameter Store.
Below is a partial example.

```yaml
NodeHelloWorldFunction:
  Type: AWS::Serverless::Function
  Properties:
  CodeUri: functions/nodeExample
  # ...
  Layers:
    - !Ref ParameterStoreCacheLayer
  Role: !GetAtt "NodeHelloWorldFunctionExecutionRole.Arn"

NodeHelloWorldFunctionExecutionRole:
  Type: AWS::IAM::Role
  Properties:
    Path: /
    PermissionsBoundary: !If
      - DeployingToLandingZoneAccount
      - !Sub "arn:aws:iam::${AWS::AccountId}:policy/LZ-IAM-Boundary"
      - !Ref "AWS::NoValue"
    ManagedPolicyArns:
      - "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    AssumeRolePolicyDocument:
      Version: "2012-10-17"
      Statement:
        - Action:
            - sts:AssumeRole
          Effect: Allow
          Principal:
            Service:
              - lambda.amazonaws.com
              - edgelambda.amazonaws.com
    Policies:
      - PolicyName: "SSMAccess"
        PolicyDocument:
          Version: "2012-10-17"
          Statement:
            - Effect: Allow
              Action:
                - ssm:GetParametersByPath
                - ssm:GetParameter
                - ssm:GetParameters
              Resource: !Sub "arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/CHANGE-ME/*"
```

If you wish to copy the file into your function, for example if you are working on a larger Layer or working with Lambda@Edge, you should
copy the `nodejs/node_modules/@elilillyco/aws-layer-ssm-parameters/index.js` file.

## Usage

Once you have the template updated you can reference the class from your node as you would any other module.

```js
const ParameterCache = require('@elilillyco/aws-layer-ssm-parameters');
new ParameterCache({ /* ... */ })
```

Ideally you would add the Layer as a dependency in your `package.json` file, but that can complicate installing dependencies
since the module is provided by the Layer. The `sam local` commands are able to take advantage of the Layer without any additional
work. For linting and unit testing you can use the [`npm link` command](https://docs.npmjs.com/cli/link). In the Layer's
root directory run `npm link`. This will set up a global reference to the package in this directory. Then in the function directory
run the command `npm link @elilillyco/aws-layer-ssm-parameters` *after* you have run `npm install`. The package of the layer installed
will be a reference to the package already on your filesystem.

The class specification for the ParameterCache is available below.

## Linting

Linting is configured to use [ESlint](https://eslint.org/) with the [Airbnb linting rules](https://www.npmjs.com/package/eslint-config-airbnb).

```bash
# Install dependencies
npm install
# Execute eslint
npm run lint
```

## Unit Testing

Testing is configured to use [Jest](https://jestjs.io/).

```bash
# Install dependencies
npm install
# Execute unit tests
npm test
```

## API

<a name="ParameterCache"></a>

### ParameterCache ⇐ <code>Map</code>
**Kind**: global variable  
**Extends**: <code>Map</code>  
**Example**  
```js
const ParameterCache = require('@elilillyco/aws-layer-ssm-parameters');
const cache = new ParameterCache({ prefix: '/ABCDEFGHIJK/', region: 'us-east-2' });

async function lambdaHandler(event) {
  // Loads parameters starting using "/ABCDEFGHIJK/" as the base path
  if(cache.size === 0) await cache.load();
  // Retrieves the value of "/ABCDEFGHIJK/my-config" from the cached values from the SSM Parameter Store
  const myConfigValue = await cache.getValue('my-config');
  // Retrieves the value of "log-level" from SSM Parameter Store
  const globalLogLevel = await cache.getValue('log-level', '');
}
```

* [ParameterCache](#ParameterCache) ⇐ <code>Map</code>
    * [new ParameterCache([options])](#new_ParameterCache_new)
    * [.load([prefix])](#ParameterCache+load) ⇒ <code>Promise.&lt;Number&gt;</code>
    * [.get(key, [prefix])](#ParameterCache+get) ⇒ [<code>Promise.&lt;Parameter&gt;</code>](#Parameter)
    * [.getValue(key, [prefix])](#ParameterCache+getValue) ⇒ <code>Promise.&lt;String&gt;</code>
    * [.has(key, [prefix])](#ParameterCache+has) ⇒ <code>Promise.&lt;Boolean&gt;</code>
    * [.delete(key, prefix)](#ParameterCache+delete) ⇒ <code>boolean</code>
    * [.refresh(key, [prefix])](#ParameterCache+refresh) ⇒ [<code>Promise.&lt;Parameter&gt;</code>](#Parameter)
    * [.refreshAll()](#ParameterCache+refreshAll) ⇒ <code>Promise.&lt;Number&gt;</code>
    * [.clearAll()](#ParameterCache+clearAll)
    * [.set()](#ParameterCache+set)

<a name="new_ParameterCache_new"></a>

#### new ParameterCache([options])

| Param | Type | Default | Description |
| --- | --- | --- | --- |
| [options] | <code>Object</code> |  |  |
| [options.prefix] | <code>String</code> | <code>/</code> | Default parameter path prefix |
| [options.withDecryption] | <code>Boolean</code> | <code>true</code> | Decrypt SecureString parameters |
| [options.region] | <code>String</code> | <code>us-east-1</code> | AWS Region |
| [options.expiresIn] | <code>Number</code> | <code>FIVE_MINUTES</code> | milliseconds |

<a name="ParameterCache+load"></a>

#### parameterCache.load([prefix]) ⇒ <code>Promise.&lt;Number&gt;</code>
Loads multiple parameters based on a path prefix.
*Uses the prefix provided when the ParameterCache object was instantiated by default*

**Queries the SSM Parameter Store**

**Kind**: instance method of [<code>ParameterCache</code>](#ParameterCache)  
**Returns**: <code>Promise.&lt;Number&gt;</code> - Number of items loaded  

| Param | Type |
| --- | --- |
| [prefix] | <code>String</code> | 

<a name="ParameterCache+get"></a>

#### parameterCache.get(key, [prefix]) ⇒ [<code>Promise.&lt;Parameter&gt;</code>](#Parameter)
Returns the Parameter object based on a key and path prefix.
*Uses the prefix provided when the ParameterCache object was instantiated by default*

If '/testPrefix/' is the prefix and 'myValue' is the key, then the `Name` of a returned
 parameter would be '/testPrefix/myValue'

**Queries the SSM Parameter Store**

**Kind**: instance method of [<code>ParameterCache</code>](#ParameterCache)  

| Param | Type |
| --- | --- |
| key | <code>String</code> | 
| [prefix] | <code>String</code> | 

<a name="ParameterCache+getValue"></a>

#### parameterCache.getValue(key, [prefix]) ⇒ <code>Promise.&lt;String&gt;</code>
Returns the Parameter value based on a key and path prefix.
*Uses the prefix provided when the ParameterCache object was instantiated by default*

If '/testPrefix/' is the prefix and 'myValue' is the key, then the `Name` of a returned
 parameter would be '/testPrefix/myValue'

**Queries the SSM Parameter Store**

**Kind**: instance method of [<code>ParameterCache</code>](#ParameterCache)  

| Param | Type |
| --- | --- |
| key | <code>String</code> | 
| [prefix] | <code>String</code> | 

<a name="ParameterCache+has"></a>

#### parameterCache.has(key, [prefix]) ⇒ <code>Promise.&lt;Boolean&gt;</code>
Returns whether the given parameter exists
*Uses the prefix provided when the ParameterCache object was instantiated by default*

**Queries the SSM Parameter Store**

**Kind**: instance method of [<code>ParameterCache</code>](#ParameterCache)  

| Param | Type |
| --- | --- |
| key | <code>String</code> | 
| [prefix] | <code>String</code> | 

<a name="ParameterCache+delete"></a>

#### parameterCache.delete(key, prefix) ⇒ <code>boolean</code>
Deletes a value from the cache.
**Does not remove the value from the SSM Parameter Store**

**Kind**: instance method of [<code>ParameterCache</code>](#ParameterCache)  

| Param | Type |
| --- | --- |
| key | <code>String</code> | 
| prefix | <code>String</code> | 

<a name="ParameterCache+refresh"></a>

#### parameterCache.refresh(key, [prefix]) ⇒ [<code>Promise.&lt;Parameter&gt;</code>](#Parameter)
Clears the key from the cache and then reloads the value from the SSM Parameter Store
*Uses the prefix provided when the ParameterCache object was instantiated by default*
**Queries the SSM Parameter Store**

**Kind**: instance method of [<code>ParameterCache</code>](#ParameterCache)  

| Param | Type |
| --- | --- |
| key | <code>String</code> | 
| [prefix] | <code>String</code> | 

<a name="ParameterCache+refreshAll"></a>

#### parameterCache.refreshAll() ⇒ <code>Promise.&lt;Number&gt;</code>
Clears the cache of all keys and reloads values from the SSM Parameter Store.
*Uses the prefix provided when the ParameterCache object was instantiated by default*
**Queries the SSM Parameter Store**

**Kind**: instance method of [<code>ParameterCache</code>](#ParameterCache)  
<a name="ParameterCache+clearAll"></a>

#### parameterCache.clearAll()
Clears the cache of all keys

**Kind**: instance method of [<code>ParameterCache</code>](#ParameterCache)  
<a name="ParameterCache+set"></a>

#### parameterCache.set()
Set method is not supported

**Kind**: instance method of [<code>ParameterCache</code>](#ParameterCache)  
**Throws**:

- Error

<a name="Parameter"></a>

### Parameter
**Kind**: global variable  
**Properties**

| Name | Type |
| --- | --- |
| name | <code>String</code> | 
| type | <code>String</code> | 
| value | <code>String</code> | 
| version | <code>Number</code> | 
| lastModifiedDate | <code>String</code> | 
| arn | <code>String</code> | 
| expiresAt | <code>Number</code> | 
