const AwsMock = require('aws-sdk-mock');
const AWS = require('aws-sdk');

AwsMock.setSDKInstance(AWS);

const ParameterCache = require('../index');

delete process.env.HTTP_PROXY;
delete process.env.HTTPS_PROXY;

const PARAMETER_ONE = {
  Name: '/sample/numberOne',
  Type: 'String',
  Value: 'ValueOne',
  Version: 1,
  LastModifiedDate: '2019-02-21T15:51:10.349Z',
  ARN: 'arn:aws:ssm:us-east-1:094060919181:parameter/sample/numberOne',
};

const PARAMETER_TWO = {
  Name: '/sample/numberTwo',
  Type: 'SecureString',
  Value: 'ValueTwo',
  Version: 2,
  LastModifiedDate: '2019-02-21T15:51:10.349Z',
  ARN: 'arn:aws:ssm:us-east-1:094060919181:parameter/sample/numberTwo',
};

const PARAMETER_THREE = {
  Name: '/sample/numberThree',
  Type: 'StringList',
  Value: 'One,Two,Three',
  Version: 3,
  LastModifiedDate: '2019-02-21T15:51:10.349Z',
  ARN: 'arn:aws:ssm:us-east-1:094060919181:parameter/sample/numberThree',
};

describe('ParameterCache', () => {
  describe('load', () => {
    let ssmMock;
    beforeEach(() => {
      ssmMock = jest.fn().mockResolvedValue({
        Parameters: [
          PARAMETER_ONE,
          PARAMETER_TWO,
          PARAMETER_THREE,
        ],
      });
      AwsMock.mock('SSM', 'getParametersByPath', ssmMock);
    });

    afterEach(() => {
      AwsMock.restore('SSM', 'getParametersByPath');
    });

    it('retrieves parameters based on the initial path prefix', async () => {
      const cache = new ParameterCache({ prefix: '/sample/' });
      expect(await cache.load()).toEqual(3);
      expect(ssmMock).toHaveBeenCalledTimes(1);
      expect(ssmMock.mock.calls[0][0]).toMatchObject({
        Path: '/sample/',
        WithDecryption: true,
        Recursive: true,
      });
    });

    it('retrieves parameters based on the prefix argument', async () => {
      const cache = new ParameterCache();
      expect(await cache.load('/sample2/')).toEqual(3);
      expect(ssmMock).toHaveBeenCalledTimes(1);
      expect(ssmMock.mock.calls[0][0]).toMatchObject({
        Path: '/sample2/',
        WithDecryption: true,
        Recursive: true,
      });
    });
  });

  describe('get', () => {
    let ssmMock;
    let cache;
    beforeAll(async () => {
      ssmMock = jest.fn().mockResolvedValue({
        Parameters: [
          PARAMETER_ONE,
        ],
      });
      AwsMock.mock('SSM', 'getParametersByPath', ssmMock);

      cache = new ParameterCache({ prefix: '/sample/' });
      await cache.load();
    });

    afterAll(() => {
      AwsMock.restore('SSM', 'getParametersByPath');
    });

    it('retrieves items from the cache', async () => {
      const result = await cache.get('numberOne');
      expect({
        Name: result.name,
        Type: result.type,
        Version: result.version,
        Value: result.value,
        LastModifiedDate: result.lastModifiedDate,
        ARN: result.arn,
      }).toMatchObject(PARAMETER_ONE);
    });

    it('retrieves unknown items from SSM', async () => {
      const mockFn = jest.fn().mockResolvedValue({
        Parameter: PARAMETER_TWO,
      });
      AwsMock.mock('SSM', 'getParameter', mockFn);

      const result = await cache.get('numberTwo');
      expect({
        Name: result.name,
        Type: result.type,
        Version: result.version,
        Value: result.value,
        LastModifiedDate: result.lastModifiedDate,
        ARN: result.arn,
      }).toMatchObject(PARAMETER_TWO);
      expect(mockFn).toHaveBeenCalledTimes(1);
      expect(mockFn.mock.calls[0][0]).toMatchObject({
        Name: '/sample/numberTwo',
        WithDecryption: true,
      });

      AwsMock.restore('SSM', 'getParameter');
    });

    it('retrieves items based on the prefix argument', async () => {
      const mockFn = jest.fn().mockResolvedValue({
        Parameter: PARAMETER_THREE,
      });
      AwsMock.mock('SSM', 'getParameter', mockFn);

      const result = await cache.get('numberThree', '/sample2/');
      expect({
        Name: result.name,
        Type: result.type,
        Version: result.version,
        Value: result.value,
        LastModifiedDate: result.lastModifiedDate,
        ARN: result.arn,
      }).toMatchObject(PARAMETER_THREE);
      expect(mockFn).toHaveBeenCalledTimes(1);
      expect(mockFn.mock.calls[0][0]).toMatchObject({
        Name: '/sample2/numberThree',
        WithDecryption: true,
      });

      AwsMock.restore('SSM', 'getParameter');
    });

    it('returns null when the item does not exist', async () => {
      const parameterNotFoundError = new Error('Test Error');
      parameterNotFoundError.name = 'ParameterNotFound';
      const mockFn = jest.fn().mockRejectedValue(parameterNotFoundError);

      AwsMock.mock('SSM', 'getParameter', mockFn);

      const result = await cache.get('testing');

      expect(result).toEqual(null);
      expect(mockFn).toHaveBeenCalledTimes(1);
    });
  });

  describe('getValue', () => {
    let ssmGetParametersByPathMock;
    let ssmGetParameterMock;
    let cache;
    beforeAll(async () => {
      ssmGetParametersByPathMock = jest.fn().mockResolvedValue({
        Parameters: [
          PARAMETER_ONE,
          PARAMETER_TWO,
          PARAMETER_THREE,
        ],
      });
      AwsMock.mock('SSM', 'getParametersByPath', ssmGetParametersByPathMock);

      const parameterNotFoundError = new Error('Test Error');
      parameterNotFoundError.name = 'ParameterNotFound';
      ssmGetParameterMock = jest.fn().mockRejectedValue(parameterNotFoundError);
      AwsMock.mock('SSM', 'getParameter', ssmGetParameterMock);

      cache = new ParameterCache({ prefix: '/sample/' });
      await cache.load();
    });

    afterAll(() => {
      AwsMock.restore('SSM', 'getParametersByPath');
      AwsMock.restore('SSM', 'getParameter');
    });

    it('returns the string value when the parameter exists', async () => {
      await expect(cache.getValue('numberOne')).resolves.toEqual(PARAMETER_ONE.Value);
    });

    it('returns null when the parameter does not exist', async () => {
      await expect(cache.getValue('unknownKey')).resolves.toEqual(null);
    });
  });

  describe('has', () => {
    it('returns true when the parameter exists', async () => {
      const cache = new ParameterCache();
      jest.spyOn(cache, 'get').mockResolvedValue({});

      expect(await cache.has('testKey')).toEqual(true);
      expect(cache.get).toHaveBeenCalledWith('testKey');

      expect(await cache.has('testKey2', '/sample/')).toEqual(true);
      expect(cache.get).toHaveBeenCalledWith('testKey2', '/sample/');
    });

    it('returns false when the parameter does not exist', async () => {
      const cache = new ParameterCache();
      jest.spyOn(cache, 'get').mockResolvedValue(null);

      expect(await cache.has('testKey')).toEqual(false);
      expect(cache.get).toHaveBeenCalledWith('testKey');

      expect(await cache.has('testKey2', '/sample/')).toEqual(false);
      expect(cache.get).toHaveBeenCalledWith('testKey2', '/sample/');
    });
  });

  describe('delete', () => {
    it('removes a cached parameter', () => {
      const cache = new ParameterCache();
      jest.spyOn(Object.getPrototypeOf(Object.getPrototypeOf(cache)), 'delete');
      cache.delete('testKey', '/sample/');
      expect(Object.getPrototypeOf(Object.getPrototypeOf(cache)).delete).toHaveBeenCalledWith('/sample/testKey');
    });
  });

  describe('refresh', () => {
    it('deletes an entry and then gets it', async () => {
      const sampleObject = {};
      const cache = new ParameterCache();
      jest.spyOn(cache, 'delete').mockReturnValue(true);
      jest.spyOn(cache, 'get').mockResolvedValue(sampleObject);

      await expect(cache.refresh('sampleKey')).resolves.toBe(sampleObject);
      expect(cache.delete).toHaveBeenNthCalledWith(1, 'sampleKey');
      expect(cache.get).toHaveBeenNthCalledWith(1, 'sampleKey');

      await expect(cache.refresh('sampleKey', '/sample/')).resolves.toBe(sampleObject);
      expect(cache.delete).toHaveBeenNthCalledWith(2, 'sampleKey', '/sample/');
      expect(cache.get).toHaveBeenNthCalledWith(2, 'sampleKey', '/sample/');
    });
  });

  describe('refreshAll', () => {
    it('calls clearAll and load', async () => {
      const cache = new ParameterCache();
      jest.spyOn(cache, 'clearAll');
      jest.spyOn(cache, 'load').mockResolvedValue(7);

      expect(await cache.refreshAll()).toEqual(7);
    });
  });

  describe('clearAll', () => {
    it('empties the cache', async () => {
      const cache = new ParameterCache();
      jest.spyOn(cache, 'clear');

      cache.clearAll();
      expect(cache.clear).toHaveBeenCalledTimes(1);
    });
  });

  describe('set', () => {
    it('throws an error', () => {
      const cache = new ParameterCache();
      expect(cache.set).toThrowError('Operation not supported');
    });
  });
});
