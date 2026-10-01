package com.ruoyi.framework.config;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertFalse;

import com.ruoyi.common.core.domain.entity.SysDictData;
import com.ruoyi.common.core.domain.entity.SysUser;
import com.ruoyi.common.core.domain.model.LoginUser;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.springframework.data.redis.serializer.SerializationException;

class SafeRedisJsonSerializerTest
{
    private final SafeRedisJsonSerializer serializer = new SafeRedisJsonSerializer();

    @Test
    void roundTripsOnlyExpectedCacheTypes()
    {
        assertEquals("captcha", serializer.deserialize(serializer.serialize("captcha")));
        assertEquals(42L, serializer.deserialize(serializer.serialize(42L)));

        SysUser user = new SysUser();
        user.setUserId(7L);
        user.setUserName("alice");
        user.setPassword("private-password-hash");
        LoginUser login = new LoginUser("tenant-1", 7L, 3L, user, Set.of("system:user:list"));
        assertEquals(List.of(), login.getAuthorities());
        byte[] encodedLogin = serializer.serialize(login);
        assertFalse(new String(encodedLogin, StandardCharsets.UTF_8).contains("private-password-hash"));
        LoginUser restored = assertInstanceOf(LoginUser.class, serializer.deserialize(encodedLogin));
        assertEquals("tenant-1", restored.getTenant());
        assertEquals(7L, restored.getUserId());
        assertEquals("alice", restored.getUser().getUserName());
        assertEquals(login.getPermissions(), restored.getPermissions());

        SysDictData data = new SysDictData();
        data.setDictValue("1");
        List<?> dictionary = assertInstanceOf(List.class, serializer.deserialize(serializer.serialize(List.of(data))));
        assertEquals("1", assertInstanceOf(SysDictData.class, dictionary.get(0)).getDictValue());

        Map<String, Object> repeat = Map.of("/route", Map.of("repeatParams", "{}", "repeatTime", 123L));
        assertEquals(repeat, serializer.deserialize(serializer.serialize(repeat)));
    }

    @Test
    void rejectsLegacyAutoTypeAndUnknownKinds()
    {
        assertThrows(SerializationException.class, () -> serializer.deserialize(
                "{\"@type\":\"java.lang.Runtime\"}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(SerializationException.class, () -> serializer.deserialize(
                "{\"version\":1,\"kind\":\"java.lang.Runtime\",\"payload\":{}}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(SerializationException.class, () -> serializer.serialize(new Object()));
        assertThrows(SerializationException.class, () -> serializer.serialize(Map.of("unsafe", List.of("nested"))));
    }

    @Test
    void rejectsCyclicAndExcessivelyNestedRedisMaps()
    {
        Map<String, Object> cycle = new HashMap<>();
        cycle.put("self", cycle);
        assertThrows(SerializationException.class, () -> serializer.serialize(cycle));

        Map<String, Object> deep = Map.of("value", "leaf");
        for (int depth = 0; depth < 40; depth++)
        {
            deep = Map.of("next", deep);
        }
        Map<String, Object> excessiveDepth = deep;
        assertThrows(SerializationException.class, () -> serializer.serialize(excessiveDepth));

        StringBuilder payload = new StringBuilder();
        for (int depth = 0; depth < 40; depth++) payload.append("{\"next\":");
        payload.append("\"leaf\"");
        for (int depth = 0; depth < 40; depth++) payload.append('}');
        byte[] encoded = ("{\"version\":1,\"kind\":\"repeat-map\",\"payload\":" + payload + "}")
                .getBytes(StandardCharsets.UTF_8);
        assertThrows(SerializationException.class, () -> serializer.deserialize(encoded));
    }
}
