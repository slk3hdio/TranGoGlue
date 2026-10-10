package cn.hutool.json;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import cn.hutool.core.lang.Filter;
import cn.hutool.core.lang.mutable.Mutable;
import cn.hutool.core.lang.mutable.MutablePair;

import org.junit.Test;

/**
 * Smoke tests for the {@link JSONParser} fragment class (cn.hutool.json.JSONParser).
 */
public class JSONParserSmokeTest {

    private static JSONParser parser(String json) {
        return new JSONParser(new JSONTokener(json, JSONConfig.create()));
    }

    @Test
    public void testOfFactoryAndParseObject() {
        JSONObject obj = new JSONObject();
        JSONParser p = JSONParser.of(new JSONTokener("{\"a\":1,\"b\":\"x\"}", JSONConfig.create()));
        assertNotNull(p);
        p.parseTo(obj, null);

        assertEquals(2, obj.size());
        assertEquals(Integer.valueOf(1), obj.get("a"));
        assertEquals(1, obj.getInt("a").intValue());
        assertEquals("x", obj.getStr("b"));
    }

    @Test
    public void testParseObjectWithSpacesAndBoolean() {
        JSONObject obj = new JSONObject();
        parser(" { \"a\" : 2 , \"b\" : true } ").parseTo(obj, null);
        assertEquals(2, obj.getInt("a").intValue());
        assertEquals(Boolean.TRUE, obj.get("b"));
    }

    @Test
    public void testParseArray() {
        JSONArray arr = new JSONArray();
        parser("[1,\"x\",true]").parseTo(arr, null);
        assertEquals(3, arr.size());
        assertEquals(1, arr.getInt(0).intValue());
        assertEquals("x", arr.getStr(1));
        assertEquals(Boolean.TRUE, arr.get(2));

        // empty array
        JSONArray empty = new JSONArray();
        parser("[]").parseTo(empty, null);
        assertEquals(0, empty.size());
    }

    @Test
    public void testInvalidInputThrows() {
        JSONObject obj = new JSONObject();
        try {
            parser("hello").parseTo(obj, null);
            fail("expected JSONException for non-object input");
        } catch (JSONException expected) {
            // expected
        }

        JSONArray arr = new JSONArray();
        try {
            parser("hello").parseTo(arr, null);
            fail("expected JSONException for non-array input");
        } catch (JSONException expected) {
            // expected
        }
    }

    @Test
    public void testParseObjectWithFilter() {
        // filter that rewrites the value of key "a" and keeps everything
        JSONObject obj = new JSONObject();
        Filter<MutablePair<String, Object>> rewrite = new Filter<MutablePair<String, Object>>() {
            public boolean accept(MutablePair<String, Object> pair) {
                if ("a".equals(pair.getKey())) {
                    pair.setValue("filtered");
                }
                return true;
            }
        };
        parser("{\"a\":\"x\",\"b\":\"y\"}").parseTo(obj, rewrite);
        assertEquals("filtered", obj.getStr("a"));
        assertEquals("y", obj.getStr("b"));

        // filter that drops key "a" entirely
        JSONObject obj2 = new JSONObject();
        Filter<MutablePair<String, Object>> drop = new Filter<MutablePair<String, Object>>() {
            public boolean accept(MutablePair<String, Object> pair) {
                return !"a".equals(pair.getKey());
            }
        };
        parser("{\"a\":\"x\",\"b\":\"y\"}").parseTo(obj2, drop);
        assertEquals(1, obj2.size());
        assertFalse(obj2.containsKey("a"));
        assertEquals("y", obj2.getStr("b"));
    }

    @Test
    public void testParseArrayWithFilter() {
        // filter that multiplies integer values by 10 and drops everything else
        JSONArray arr = new JSONArray();
        Filter<Mutable<Object>> filter = new Filter<Mutable<Object>>() {
            public boolean accept(Mutable<Object> mutable) {
                Object v = mutable.get();
                if (v instanceof Integer) {
                    mutable.set(((Integer) v).intValue() * 10);
                    return true;
                }
                return false;
            }
        };
        parser("[1,\"x\",2]").parseTo(arr, filter);
        assertEquals(2, arr.size());
        assertEquals(10, arr.getInt(0).intValue());
        assertEquals(20, arr.getInt(1).intValue());
    }
}
