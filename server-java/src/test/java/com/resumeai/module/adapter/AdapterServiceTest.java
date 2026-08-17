package com.resumeai.module.adapter;

import com.resumeai.module.adapter.dto.AdapterEnableResponse;
import com.resumeai.module.adapter.dto.AdapterInfo;
import com.resumeai.module.adapter.dto.AdaptersListResponse;
import com.resumeai.module.adapter.entity.AdapterRegistry;
import com.resumeai.module.adapter.repository.AdapterRegistryRepository;
import com.resumeai.module.adapter.repository.UserAdapterRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** A14 / A15 关键路径单测（H2 内存库）。 */
@SpringBootTest
class AdapterServiceTest {

    @Autowired
    private AdapterRegistryRepository registryRepo;
    @Autowired
    private UserAdapterRepository userAdapterRepo;
    @Autowired
    private AdapterService svc;

    private void seedRegistry(String platform, String version) {
        AdapterRegistry r = new AdapterRegistry();
        r.setPlatformId(platform);
        r.setVersion(version);
        r.setStatus("active");
        r.setCreatedAt(100L);
        registryRepo.save(r);
    }

    @Test
    void list_returnsActiveAdapters_defaultEnabled() {
        seedRegistry("boss", "1.0.0");
        seedRegistry("liepin", "1.0.0");

        AdaptersListResponse res = svc.list("u-1");
        assertEquals(2, res.items().size());
        assertTrue(res.items().stream().allMatch(i -> "enabled".equals(i.status())));
    }

    @Test
    void enable_disablesAdapter_thenListReflects() {
        seedRegistry("boss", "1.0.0");
        seedRegistry("liepin", "1.0.0");

        AdapterEnableResponse r = svc.enable("u-1", "boss", false);
        assertEquals("boss", r.adapterId());
        assertEquals("disabled", r.status());

        AdaptersListResponse res = svc.list("u-1");
        Optional<AdapterInfo> boss = res.items().stream()
                .filter(i -> "boss".equals(i.platform())).findFirst();
        assertTrue(boss.isPresent());
        assertEquals("disabled", boss.get().status());

        List<AdapterInfo> liepin = res.items().stream()
                .filter(i -> "liepin".equals(i.platform())).toList();
        assertFalse(liepin.isEmpty());
        assertEquals("enabled", liepin.get(0).status());
    }
}
