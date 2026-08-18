package com.resumeai.module.adapter.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.adapter.entity.AdapterRegistry;
import org.springframework.stereotype.Repository;


/** 适配器包元数据存储（adapter_registry · 全局）。 */
@Repository
public interface AdapterRegistryRepository extends BaseMapper<AdapterRegistry> {


    default AdapterRegistry save(AdapterRegistry e) {
        QueryWrapper<AdapterRegistry> q = new QueryWrapper<AdapterRegistry>()
                .eq("platform_id", e.getPlatformId()).eq("version", e.getVersion());
        if (selectOne(q) != null) {
            update(e, new UpdateWrapper<AdapterRegistry>()
                    .eq("platform_id", e.getPlatformId()).eq("version", e.getVersion()));
        } else {
            insert(e);
        }
        return e;
    }
    default List<AdapterRegistry> findByStatus(String status) {
        return selectList(new QueryWrapper<AdapterRegistry>().eq("status", status));
    }

}
