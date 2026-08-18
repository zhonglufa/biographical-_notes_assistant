package com.resumeai.module.adapter.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;
import com.resumeai.module.adapter.entity.AdapterRegistry;
import org.springframework.stereotype.Repository;

@Mapper
@Repository
public interface AdapterRegistryMapper extends BaseMapper<AdapterRegistry> {

    default AdapterRegistry save(AdapterRegistry e) { insert(e); return e; }

    default List<AdapterRegistry> findByStatus(String status) {
        return selectList(new QueryWrapper<AdapterRegistry>().eq("status", status));
    }

}
