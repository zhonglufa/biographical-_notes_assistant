package com.resumeai.module.adapter.repository;

import com.resumeai.module.adapter.entity.AdapterRegistry;
import com.resumeai.module.adapter.entity.AdapterRegistryId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/** 适配器包元数据存储（adapter_registry · 全局）。 */
@Repository
public interface AdapterRegistryRepository extends JpaRepository<AdapterRegistry, AdapterRegistryId> {
    List<AdapterRegistry> findByStatus(String status);
}
