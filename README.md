# mdids-regintel-processbatch


## Getting Started

If you haven't already you should create a GitHub repository for this project via [ServiceNow](https://lilly.service-now.com), search for "GitHub Services". You can clone the repository that ServiceNow creates
and copy your project files into that new directory. Once you have copied your files over it is heavily recommended to create an initial commit with the files exactly as they were
created. This provides a point in the git history where you can find what what originally created for you.

You should create a Jenkins job through [ServiceNow](https://lilly.service-now.com) if you have not already, you can search for "Jenkins Services" to find the correct request.
Select "AWS" as the platform. Details about the AWS Jenkins pipeline can be found in the [cirr-jenkins-aws-templates GitHub repository](https://github.com/EliLillyCo/cirr-jenkins-aws-templates).

In AWS Landing Zone accounts the HCS AWS CICD release pipeline is being used. **At the time of writing this has not yet been fully configured.** The release pipeline begins after Jenkins has tested your project and uploaded
your code to AWS. From there the release pipeline will pick up your code and deploy it to your landing zone development environment. Then it will continue on and deploy to your QA landing zone environment, after checking for
an approval. Then it will deploy to your production landing zone environment, again, after an approval.

Details about the requirements and features of the deployment pipeline can be found in the [GIS_HCS_AWS_CICD GitHub repository](https://github.com/EliLillyCo/GIS_HCS_AWS_CICD/blob/master/docs/release-pipelines/README.md).


## Directory Structure

```
.
├── README.MD                         <-- This instructions file
├── functions                         <-- Directory for lambda function's source code
│   ├── nodeExample
│   │   ├── index.js                  <-- Lambda function code
│   │   ├── package.json              <-- NodeJS dependencies and scripts
│   │   └── tests                     <-- Unit tests
│   │       └── index.test.js
│   └── pythonExample
│       ├── app.py                    <-- Lambda function code
│       ├── requirements.txt          <-- Python dependencies
│       └── tests                     <-- Unit tests
│           └── test_handler.py
└── template.yaml                     <-- SAM CloudFormation template
```

## Lambda Function Best Practices

Read about AWS Lambda Best Practices [on this page](https://github.com/EliLillyCo/cirr-aws-landing-zone-api/blob/master/docs/lambda-function-best-practices.md).
