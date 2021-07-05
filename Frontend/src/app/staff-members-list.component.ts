import { Component } from '@angular/core';
import {FormBuilder, Validators} from '@angular/forms';
import { BackendService } from './backendService';

@Component({
    selector: 'staffMembersList',
    templateUrl: './staff-members-List.component.html',
    styleUrls: ['./staff-members-List.component.css']
})
export class StaffMembersListComponent {

    staffMemberForm;
    addStaffMember = false

    constructor(private backendService: BackendService,
        private formBuilder: FormBuilder) {}

    async ngOnInit(){
        if(this.addStaffMember == true)
        {
            this.getAddForm();
        }
        else
        {
             this.backendService.employeeListRefreshNedded
             .subscribe(() => {
                this.backendService.getStaffMembers();
             });
             this.backendService.getStaffMembers();
        }      
    }

    getAddForm(){
        this.staffMemberForm = this.formBuilder.group({
            firstName: ['', Validators.required],            
            surname: ['', Validators.required],
            address: ['', Validators.required],
            city: ['', Validators.required],
            region: ['UK', Validators.required],
            mobile: ['', Validators.required]
        });
    }

    addButtonClicked(){
        this.addStaffMember = true
        this.ngOnInit();
    }

    cancelButtonClicked(){
            this.addStaffMember = false
            this.ngOnInit()  
    }

    onSubmit(){
        this.backendService.addStaffMember(this.staffMemberForm.value).subscribe();
        this.addStaffMember = false
        this.ngOnInit();
    }

    isInvalid(control) {
        return this.staffMemberForm.controls[control].invalid &&
                this.staffMemberForm.controls[control].touched;
            }
    
    isIncomplete() {
        return this.isInvalid('firstName') ||
                this.isInvalid('surname') ||
                this.isInvalid('address') ||
                this.isInvalid('city') ||
                this.isInvalid('region') ||
                this.isInvalid('mobile') ||
                this.isUnTouched();
    }

    isUnTouched() {
        return this.staffMemberForm.controls.firstName.pristine ||
                this.staffMemberForm.controls.surname.pristine ||
                this.staffMemberForm.controls.address.pristine ||
                this.staffMemberForm.controls.city.pristine ||
                this.staffMemberForm.controls.mobile.pristine;
    }
}