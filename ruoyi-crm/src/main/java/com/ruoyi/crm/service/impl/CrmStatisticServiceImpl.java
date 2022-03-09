package com.ruoyi.crm.service.impl;

import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.crm.domain.CrmCustomer;
import com.ruoyi.crm.domain.enums.CustomerFolder;
import com.ruoyi.crm.service.ICrmStatisticService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * @Author: devjd
 * @Date: 2022/1/27
 * @Description:
 */
@Service
public class CrmStatisticServiceImpl implements ICrmStatisticService {

    @Autowired
    private CrmCustomerServiceImpl customerService;

    /**
     * 跟进信息
     * @return
     */
    @Override
    public Map<String, Object> followupInfo(String owner) {
        Map<String, Object> map = new HashMap<>();

        CrmCustomer crmCustomer = new CrmCustomer();
        crmCustomer.setStatus(CustomerFolder.CUSTOMER.getCode());
        crmCustomer.setOwner(owner);

        Map<String, Object> params = new HashMap<>();
        //今日已经跟进个数
        params.put("beginLastFollowupTime", DateUtils.getDate());
        params.put("endLastFollowupTime", DateUtils.getDate());
        crmCustomer.setParams(params);
        List<CrmCustomer> lastFollowup = customerService.selectCrmCustomerList(crmCustomer);
        Integer lastFollowupCount=lastFollowup.size();
        map.put("today_followup", lastFollowupCount);

        params.clear();
        //今日待跟进个数
        params.put("beginNextFollowupTime", DateUtils.getDate());
        params.put("endNextFollowupTime", DateUtils.getDate());
        crmCustomer.setParams(params);
        List<CrmCustomer> nextFollowup = customerService.selectCrmCustomerList(crmCustomer);
        Integer nextFollowupCount=nextFollowup.size();


        //今日需跟进合计=今日已经跟进个数+今日待跟进个数
        Integer totalFollowup=lastFollowupCount+nextFollowupCount;

        //未跟进个数=今日需跟进合计-已跟进
        Integer noFollowupCount=totalFollowup-lastFollowupCount;
        map.put("no_followup", noFollowupCount);

        //跟进率=已经跟进/待跟进
        map.put("followup_rate",totalFollowup!=0?((lastFollowupCount / totalFollowup)*100):0 );

        return map;
    }

    @Override
    public Map<String, Object> customerInfo(String owner){

        Map<String, Object> map=new HashMap<>();

        CrmCustomer crmCustomer=new CrmCustomer();

        crmCustomer.setStatus(CustomerFolder.CLUES.getCode());
        List<CrmCustomer> cluesCustomers = customerService.selectCrmCustomerList(crmCustomer);
        Long myClues=cluesCustomers.stream().filter(e->e.getOwner().equals(owner)).count();
        Integer cluesTotal=cluesCustomers.size();
        map.put("my_clues", myClues);
        map.put("clues_total", cluesTotal);

        crmCustomer.setStatus(CustomerFolder.CUSTOMER.getCode());
        List<CrmCustomer> customers = customerService.selectCrmCustomerList(crmCustomer);
        Long myCustomers=customers.stream().filter(e->e.getOwner().equals(owner)).count();
        Integer customerTotal=customers.size();
        map.put("my_customers", myCustomers);
        map.put("customer_total", customerTotal);

        crmCustomer.setStatus(CustomerFolder.POOL.getCode());
        List<CrmCustomer> pools = customerService.selectCrmCustomerList(crmCustomer);
        Integer poolTotals=pools.size();
        map.put("my_pools", poolTotals);
        map.put("pool_total", poolTotals);


        return map;
    }

    @Override
    public List<CrmCustomer> todayFollowupList(String owner) {
        CrmCustomer crmCustomer = new CrmCustomer();
        crmCustomer.setStatus(CustomerFolder.CUSTOMER.getCode());
        crmCustomer.setOwner(owner);
        Map<String, Object> params = new HashMap<>();
        params.put("beginNextFollowupTime", DateUtils.getDate());
        params.put("endNextFollowupTime", DateUtils.getDate());
        crmCustomer.setParams(params);
        List<CrmCustomer> nextFollowup = customerService.selectCrmCustomerList(crmCustomer);
        return nextFollowup;
    }
}
