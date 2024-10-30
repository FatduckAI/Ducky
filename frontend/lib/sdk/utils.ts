/**
 * Case conversion utilities
 */
function toSnakeCase(str: string): string {
  return str
    .replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`)
    .replace(/^_/, "");
}

function toCamelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

function toSnakeCaseKeys<T extends object>(obj: T): any {
  if (Array.isArray(obj)) {
    return obj.map((item) =>
      typeof item === "object" && item !== null ? toSnakeCaseKeys(item) : item
    );
  }

  return Object.entries(obj).reduce((acc, [key, value]) => {
    const snakeKey = toSnakeCase(key);
    const transformedValue =
      typeof value === "object" && value !== null
        ? toSnakeCaseKeys(value)
        : value;

    return { ...acc, [snakeKey]: transformedValue };
  }, {});
}

function toCamelCaseKeys<T extends object>(obj: T): any {
  if (Array.isArray(obj)) {
    return obj.map((item) =>
      typeof item === "object" && item !== null ? toCamelCaseKeys(item) : item
    );
  }

  return Object.entries(obj).reduce((acc, [key, value]) => {
    const camelKey = toCamelCase(key);
    const transformedValue =
      typeof value === "object" && value !== null
        ? toCamelCaseKeys(value)
        : value;

    return { ...acc, [camelKey]: transformedValue };
  }, {});
}

export { toCamelCaseKeys, toSnakeCaseKeys };
