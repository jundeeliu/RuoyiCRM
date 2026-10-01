package com.ruoyi.common.utils;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

/** JSON handling without polymorphic class loading from input. */
public final class JsonUtils
{
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private JsonUtils()
    {
    }

    public static String toJson(Object value)
    {
        try
        {
            return MAPPER.writeValueAsString(value);
        }
        catch (JsonProcessingException e)
        {
            throw new IllegalArgumentException("Cannot encode JSON value", e);
        }
    }

    public static JsonNode parseTree(String value)
    {
        try
        {
            return MAPPER.readTree(value);
        }
        catch (JsonProcessingException e)
        {
            throw new IllegalArgumentException("Cannot parse JSON value", e);
        }
    }
}
