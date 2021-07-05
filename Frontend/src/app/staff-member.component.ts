import { Component } from '@angular/core';
import {FormBuilder, Validators} from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { BackendService } from './backendService';

@Component({
    selector: 'staffMember',
    templateUrl: './staff-member.component.html',
    styleUrls: ['./staff-member.component.css']
})
export class StaffMemberComponent {

    editStaffMember = false
    deleteStaffMember = false
    staffMemberForm;

    // Variables for editing a staff member 
    staffID = ''
    firstName = ''
    surname = ''
    address = ''
    city = ''
    region = ''
    mobile = ''

    constructor(private backendService: BackendService,
        private formBuilder: FormBuilder,
        private route: ActivatedRoute,
        private router: Router) {}

    ngOnInit(){
        if (this.editStaffMember == true)
        {
            this.getEditForm();
        }
        else
        {
            this.backendService.getEmployee(this.route.snapshot.params.id);
        }
    }

    getEditForm(){
        this.staffMemberForm = this.formBuilder.group({
            firstName: [this.firstName, Validators.required],            
            surname: [this.surname, Validators.required],
            address: [this.address, Validators.required],
            city: [this.city, Validators.required],
            region: [this.region, Validators.required],
            mobile: [this.mobile, Validators.required]
        });
    }

    editButtonClicked(id, firstName, surname, address, city, region, mobile){
        this.editStaffMember = true
        this.staffID = id
        this.firstName = firstName
        this.surname = surname
        this.address = address
        this.city = city
        this.region = region
        this.mobile = mobile
        this.ngOnInit();
    }

    onSubmit(){
        this.backendService.editStaffMember(this.staffID , this.staffMemberForm.value).subscribe();
        this.editStaffMember = false
         this.ngOnInit();
    }
    
    cancelButtonClicked(){
        if (this.editStaffMember == true){
            this.editStaffMember = false
        }
        else if (this.deleteStaffMember == true){
            this.deleteStaffMember = false
        }
        this.ngOnInit()
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
                this.isInvalid('mobile') 
    }

    deleteButtonClicked(id){
        this.staffID = id
        this.deleteStaffMember = true
        this.ngOnInit()
    }

    confirmDeletion(){
        this.backendService.deleteStaffMember(this.staffID)
        this.router.routeReuseStrategy.shouldReuseRoute = () => false;
        this.router.onSameUrlNavigation = 'reload';
        this.router.navigate(['/staffmembers']);
    }
}