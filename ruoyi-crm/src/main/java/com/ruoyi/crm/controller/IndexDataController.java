package com.ruoyi.crm.controller;

import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.crm.domain.CrmCustomer;
import com.ruoyi.crm.domain.enums.CustomerFolder;
import com.ruoyi.crm.service.ICrmCustomerService;
import com.ruoyi.crm.vo.TodayUpdatesVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * @Author: eddie
 * @Date: 2022/1/19
 * @Description:
 */
@RestController
@RequestMapping("/crm/index-data")
public class IndexDataController extends BaseController {


    @Autowired
    private ICrmCustomerService customerService;

    @GetMapping("/info")
    public AjaxResult indexData(){
        Map<String,Object> result=new HashMap<>();
        Map<String, Object> customerInfo = customerInfo();
        result.put("customer_info",customerInfo );

        Map<String, Object> followupInfo = followupInfo();
        result.put("followup_info", followupInfo);

        List<CrmCustomer> todayFollowupList = todayFollowupList();
        result.put("today_followup_list", todayFollowupList);

        List<TodayUpdatesVO> todayUpdatesList = customerService.todayUpdates(getUsername());
        result.put("today_updates", todayUpdatesList);

        return AjaxResult.success(result);
    }

    private Map<String, Object> customerInfo(){

        Map<String, Object> map=new HashMap<>();

        CrmCustomer crmCustomer=new CrmCustomer();

        crmCustomer.setStatus(CustomerFolder.CLUES.getCode());
        List<CrmCustomer> cluesCustomers = customerService.selectCrmCustomerList(crmCustomer);
        Long myClues=cluesCustomers.stream().filter(e->e.getOwner().equals(getUsername())).count();
        Integer cluesTotal=cluesCustomers.size();
        map.put("my_clues", myClues);
        map.put("clues_total", cluesTotal);

        crmCustomer.setStatus(CustomerFolder.CUSTOMER.getCode());
        List<CrmCustomer> customers = customerService.selectCrmCustomerList(crmCustomer);
        Long myCustomers=customers.stream().filter(e->e.getOwner().equals(getUsername())).count();
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

    private Map<String, Object> followupInfo() {
        Map<String, Object> map = new HashMap<>();

        CrmCustomer crmCustomer = new CrmCustomer();
        crmCustomer.setStatus(CustomerFolder.CUSTOMER.getCode());
        crmCustomer.setOwner(getUsername());

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

    private List<CrmCustomer> todayFollowupList() {
        CrmCustomer crmCustomer = new CrmCustomer();
        crmCustomer.setStatus(CustomerFolder.CUSTOMER.getCode());
        crmCustomer.setOwner(getUsername());
        Map<String, Object> params = new HashMap<>();
        params.put("beginNextFollowupTime", DateUtils.getDate());
        params.put("endNextFollowupTime", DateUtils.getDate());
        crmCustomer.setParams(params);
        List<CrmCustomer> nextFollowup = customerService.selectCrmCustomerList(crmCustomer);
        return nextFollowup;
    }
}
