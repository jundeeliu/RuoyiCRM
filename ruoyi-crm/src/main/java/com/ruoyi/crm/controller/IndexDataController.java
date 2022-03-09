package com.ruoyi.crm.controller;

import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.crm.domain.CrmCustomer;
import com.ruoyi.crm.domain.enums.CustomerFolder;
import com.ruoyi.crm.service.ICrmCustomerService;
import com.ruoyi.crm.service.ICrmStatisticService;
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

    @Autowired
    private ICrmStatisticService statisticService;

    @GetMapping("/info")
    public AjaxResult indexData(){
        Map<String,Object> result=new HashMap<>();
        Map<String, Object> customerInfo = statisticService.customerInfo(getUsername());
        result.put("customer_info",customerInfo );

        Map<String, Object> followupInfo = statisticService.followupInfo(getUsername());
        result.put("followup_info", followupInfo);

        List<CrmCustomer> todayFollowupList = statisticService.todayFollowupList(getUsername());
        result.put("today_followup_list", todayFollowupList);

        List<TodayUpdatesVO> todayUpdatesList = customerService.todayUpdates(getUsername());
        result.put("today_updates", todayUpdatesList);

        return AjaxResult.success(result);
    }

}
