import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { DatePipe, formatDate } from '@angular/common';
import { Subject} from 'rxjs';
import {tap} from 'rxjs/operators';

@Injectable()
export class BackendService{

    //Assigning HTTP request results to variables that can be read by the frontend

    private staffMemberList;
    private staffSubject = new Subject();
    staffMembers = this.staffSubject.asObservable();

    private employeeDetails;
    private employeeSubject = new Subject();
    employee = this.employeeSubject.asObservable();

    private coverHistoryList;
    private coverHistorySubject = new Subject();
    coverHistory = this.coverHistorySubject.asObservable();

    private requestDetails;
    private coverRequestSubject = new Subject();
    coverRequest = this.coverRequestSubject.asObservable()

    private shopsList;
    private shopsSubject = new Subject();
    allShops = this.shopsSubject.asObservable()

    private shopDetails;
    private singleShopSubject = new Subject();
    shop = this.singleShopSubject.asObservable()

    private _refreshEmployeeList = new Subject<void>();
    get employeeListRefreshNedded() {
        return this._refreshEmployeeList
    }

    private _refreshCoverRequest = new Subject<void>();
    get coverRequestRefreshNeeded() {
        return this._refreshCoverRequest
    }

    private _refreshShopsList = new Subject<void>();
    get shopsListRefreshNeeded(){
        return this._refreshShopsList
    }

    constructor(private http: HttpClient,
        private datepipe: DatePipe) {}

    //HTTP Requests

    getStaffMembers() {
        return this.http.get('http://localhost:5000/api/v1.0/staffmembers')
        .subscribe(response => {
            this.staffMemberList = response;
            this.staffSubject.next(this.staffMemberList);
        })
    }

    getEmployee(staffID){
        return this.http.get('http://localhost:5000/api/v1.0/staffmembers/' + staffID)
        .subscribe(response => {
            this.employeeDetails = response;
            this.employeeSubject.next(this.employeeDetails);
        })
    }

    getCoverHistory(){
        return this.http.get('http://localhost:5000/api/v1.0/coverhistory')
        .subscribe(response => {
            this.coverHistoryList = response;
            this.coverHistorySubject.next(this.coverHistoryList);
        })
    }

    getCoverRequest(requestID){
        return this.http.get('http://localhost:5000/api/v1.0/coverhistory/' + requestID)
        .subscribe(response => {
            this.requestDetails = response;
            this.coverRequestSubject.next(this.requestDetails);
        })
    }

    getNumberOfRecipients(form){
        return this.http.get<any>('http://localhost:5000/api/v1.0/numberofrecipients?travelTime=' + form.timeFilter + "&distance=" 
        + form.distanceFilter + "&store=" + form.store.shopName)
                .pipe();
    }

    getAllShops() {
        return this.http.get('http://localhost:5000/api/v1.0/shops')
        .subscribe(response => {
            this.shopsList = response;
            this.shopsSubject.next(this.shopsList);
        })
    }

    getAllShopNames(){
        return this.http.get<any>('http://localhost:5000/api/v1.0/shops/names')
        .pipe();
    }

    getSingleShop(shopID){
        return this.http.get('http://localhost:5000/api/v1.0/shops/' + shopID)
        .subscribe(response => {
            this.shopDetails = response;
            this.singleShopSubject.next(this.shopDetails);
        })
    }

    addShop(form){
        let requestData = new FormData();
        requestData.append("shopName", form.shopName);
        requestData.append("address", form.address);
        requestData.append("city", form.city);
        requestData.append("region", form.region);

        return this.http.post(
            'http://localhost:5000/api/v1.0/shops', requestData)
            .pipe(tap(() => { this._refreshShopsList.next();
            })
        );
    }

    editShop(shopID, form){
        let requestData = new FormData();
        requestData.append("shopName", form.shopName);
        requestData.append("address", form.address);
        requestData.append("city", form.city);
        requestData.append("region", form.region);

        return this.http.put(
            'http://localhost:5000/api/v1.0/shops/' + shopID, requestData)
            .pipe(tap(() => { this.getSingleShop(shopID);
            })
        );
    }
    
    deleteShop(shopID){
        this.http.delete('http://localhost:5000/api/v1.0/shops/' + shopID).subscribe(
            response => {this.getAllShops();} 
            );
    }

    editStaffMember(staffID, form){
        let requestData = new FormData();
        requestData.append("firstName", form.firstName);
        requestData.append("surname", form.surname);
        requestData.append("address", form.address);
        requestData.append("city", form.city);
        requestData.append("region", form.region);
        requestData.append("mobile", form.mobile);

        return this.http.put(
            'http://localhost:5000/api/v1.0/staffmembers/' + staffID, requestData)
            .pipe(tap(() => { this.getEmployee(staffID);
            })
        );
    }   
    
    sendCoverRequest(form) {
        let creationDate = formatDate(Date.now(), 'dd-MM-yyyy', 'en')
        let requestData = new FormData();
        let shiftDate = this.datepipe.transform(form.date, 'EEEE d MMMM y')
        requestData.append("creationDate", creationDate)
        requestData.append("store", form.store.shopName);
        requestData.append("role", form.role);
        requestData.append("date", shiftDate);
        requestData.append("startTime", form.startTime);
        requestData.append("endTime", form.endTime);

        this.http.post(
                'http://localhost:5000/api/v1.0/sendmessage?travelTime=' + form.timeFilter + "&distance=" + form.distanceFilter, requestData)
                .subscribe(response => {window.alert("Request Successfully Created");
                });
    } 

    cancelCoverRequest(requestID){
       this.http.put(
        'http://localhost:5000/api/v1.0/coverhistory/' + requestID + "/cancel", null)
        .subscribe(response => {this.getCoverRequest(requestID);
            this._refreshCoverRequest == response;
        });
    }

    addStaffMember(form) {
        let requestData = new FormData();
        requestData.append("firstName", form.firstName);
        requestData.append("surname", form.surname);
        requestData.append("address", form.address);
        requestData.append("city", form.city);
        requestData.append("region", form.region);
        requestData.append("mobile", form.mobile);

        return this.http.post(
            'http://localhost:5000/api/v1.0/staffmembers', requestData)
            .pipe(tap(() => { this._refreshEmployeeList.next();
            })
        );
    }
    
    deleteStaffMember(staffID){
        this.http.delete('http://localhost:5000/api/v1.0/staffmembers/' + staffID).subscribe(
            response => {this.getStaffMembers();} 
            );
    }

}